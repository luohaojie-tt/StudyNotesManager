"""Vector search service using ChromaDB."""

import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from loguru import logger
from openai import AsyncOpenAI

from app.core.config import get_settings

settings = get_settings()


class VectorSearchService:
    """Service for vector search using ChromaDB and OpenAI embeddings."""

    def __init__(self) -> None:
        """Initialize vector search service."""
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Initialize OpenAI client for embeddings
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Collection name
        self.collection_name = "note_embeddings"
        self.collection = None

    async def initialize(self) -> None:
        """Initialize collection (call this on startup)."""
        try:
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Initialized ChromaDB collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    async def index_note(
        self,
        note_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Index note content for vector search.

        Args:
            note_id: Note ID
            content: Note text content
            metadata: Additional metadata (title, page, etc.)
        """
        try:
            # Split content into chunks (for better retrieval)
            chunks = self._chunk_text(content, chunk_size=500, overlap=50)

            # Generate embeddings for each chunk
            embeddings = []
            for chunk in chunks:
                embedding = await self._generate_embedding(chunk)
                embeddings.append(embedding)

            # Prepare metadata for each chunk
            ids = [f"{note_id}_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "note_id": note_id,
                    "chunk_index": i,
                    **(metadata or {}),
                }
                for i in range(len(chunks))
            ]

            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
            )

            logger.info(f"Indexed note {note_id} with {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Failed to index note {note_id}: {e}")
            raise

    async def search_similar_content(
        self,
        query: str,
        note_id: Optional[str] = None,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Search for similar content.

        Args:
            query: Search query
            note_id: Optional note ID to filter by
            top_k: Number of results to return

        Returns:
            List of similar content with metadata
        """
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)

            # Build where filter
            where_filter = None
            if note_id:
                where_filter = {"note_id": note_id}

            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
            )

            # Format results
            formatted_results = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    similarity = 1 - results["distances"][0][i]  # Convert cosine distance to similarity

                    # Apply threshold
                    if similarity < settings.VECTOR_SIMILARITY_THRESHOLD:
                        continue

                    formatted_results.append({
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "similarity": similarity,
                    })

            logger.info(f"Found {len(formatted_results)} similar results for query")
            return formatted_results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def find_relevant_snippets_for_wrong_answer(
        self,
        question: str,
        user_answer: str,
        correct_answer: str,
        note_id: str,
    ) -> List[Dict[str, Any]]:
        """Find relevant note snippets for a wrong answer.

        Args:
            question: Quiz question
            user_answer: User's incorrect answer
            correct_answer: Correct answer
            note_id: Note ID to search in

        Returns:
            List of relevant note snippets
        """
        # Build search query combining question and incorrect answer
        search_query = f"Question: {question}. Understanding about: {correct_answer}"

        # Search for relevant content
        results = await self.search_similar_content(
            query=search_query,
            note_id=note_id,
            top_k=settings.VECTOR_SEARCH_TOP_K,
        )

        logger.info(f"Found {len(results)} relevant snippets for wrong answer")
        return results

    async def delete_note(self, note_id: str) -> None:
        """Delete note from index.

        Args:
            note_id: Note ID
        """
        try:
            # Get all IDs for this note
            results = self.collection.get(where={"note_id": note_id})

            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted note {note_id} from vector index")

        except Exception as e:
            logger.error(f"Failed to delete note {note_id} from index: {e}")
            raise

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        try:
            response = await self.openai_client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text,
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> List[str]:
        """Split text into chunks.

        Args:
            text: Input text
            chunk_size: Maximum chunk size (in characters)
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < text_length:
                last_period = chunk.rfind("。")
                last_newline = chunk.rfind("\n")
                break_point = max(last_period, last_newline)

                if break_point > chunk_size * 0.5:  # At least 50% of chunk
                    chunk = text[start : start + break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

    async def close(self) -> None:
        """Close service connections."""
        await self.openai_client.close()
