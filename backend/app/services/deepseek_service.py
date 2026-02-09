"""DeepSeek API integration service."""

import json
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from app.core.config import get_settings

settings = get_settings()

# Module-level shared HTTP client to prevent resource leaks
_shared_client: Optional[httpx.AsyncClient] = None


def get_shared_client() -> httpx.AsyncClient:
    """Get or create shared HTTP client for DeepSeek API.

    Returns:
        Shared AsyncClient instance
    """
    global _shared_client
    if _shared_client is None:
        _shared_client = httpx.AsyncClient(
            base_url=settings.DEEPSEEK_BASE_URL,
            headers={
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        logger.info("Created shared DeepSeek HTTP client")
    return _shared_client


async def close_shared_client() -> None:
    """Close shared HTTP client. Should be called on application shutdown."""
    global _shared_client
    if _shared_client is not None:
        await _shared_client.aclose()
        _shared_client = None
        logger.info("Closed shared DeepSeek HTTP client")


class DeepSeekService:
    """Service for interacting with DeepSeek API."""

    def __init__(self) -> None:
        """Initialize DeepSeek service with shared HTTP client."""
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
        # Use shared client to prevent resource leaks
        self.client = get_shared_client()

    async def close(self) -> None:
        """Close HTTP client.

        Note: Individual service instances no longer close the shared client.
        Use close_shared_client() on application shutdown instead.
        """
        # Shared client is managed at module level
        # This method is kept for backwards compatibility but does nothing
        logger.debug("DeepSeekService.close() called - shared client not closed")

    async def _make_request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Make API request with retry logic.

        Args:
            endpoint: API endpoint
            data: Request payload
            max_retries: Maximum number of retries

        Returns:
            API response

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        for attempt in range(max_retries):
            try:
                response = await self.client.post(endpoint, json=data)
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.warning(f"DeepSeek API request failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise
                await self._handle_error(e.response.status_code)

            except httpx.RequestError as e:
                logger.error(f"DeepSeek API request error: {e}")
                raise

        return {}  # Should never reach here

    async def _handle_error(self, status_code: int) -> None:
        """Handle API errors with appropriate backoff.

        Args:
            status_code: HTTP status code
        """
        import asyncio

        if status_code == 429:  # Rate limit
            wait_time = 2.0
            logger.warning(f"Rate limit hit, waiting {wait_time}s")
            await asyncio.sleep(wait_time)
        elif status_code >= 500:  # Server error
            wait_time = 1.0
            logger.warning(f"Server error, waiting {wait_time}s")
            await asyncio.sleep(wait_time)

    async def generate_completion(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        model: str = "deepseek-chat",
    ) -> str:
        """Generate text completion.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            model: Model name

        Returns:
            Generated text
        """
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        response = await self._make_request("/chat/completions", data)
        return response["choices"][0]["message"]["content"]

    async def generate_mindmap(
        self,
        note_content: str,
        note_title: str,
        max_levels: int = 5,
    ) -> Dict[str, Any]:
        """Generate mindmap structure from note content.

        Args:
            note_content: Note text content
            note_title: Note title
            max_levels: Maximum hierarchy levels

        Returns:
            Mindmap structure as nested dictionary

        Raises:
            ValueError: If note content is too long
            json.JSONDecodeError: If response is not valid JSON
        """
        # Validate input length
        import tiktoken

        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        token_count = len(encoding.encode(note_content))

        if token_count > settings.MAX_TOKENS_PER_NOTE:
            logger.warning(
                f"Note content too long ({token_count} tokens), truncating to {settings.MAX_TOKENS_PER_NOTE}"
            )
            # Truncate from the beginning (keep most recent content)
            note_content = encoding.decode(
                encoding.encode(note_content)[-settings.MAX_TOKENS_PER_NOTE :]
            )

        prompt = self._get_mindmap_prompt(note_title, note_content, max_levels)

        try:
            response = await self.generate_completion(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for more structured output
            )

            # Extract JSON from response
            json_str = self._extract_json(response)
            mindmap_structure = json.loads(json_str)

            # Validate structure
            self._validate_mindmap_structure(mindmap_structure, max_levels)

            return mindmap_structure

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse mindmap JSON: {e}")
            raise ValueError(f"Invalid mindmap structure returned: {e}")

        except Exception as e:
            logger.error(f"Mindmap generation failed: {e}")
            raise

    def _sanitize_for_prompt(self, text: str) -> str:
        """Sanitize user input to prevent prompt injection.

        Args:
            text: User input text

        Returns:
            Sanitized text
        """
        # Remove potential prompt injection patterns
        import re

        # Remove common injection patterns
        injection_patterns = [
            r"(?i)ignore\s+(all\s+)?(previous|above|the)\s+instructions",
            r"(?i)disregard\s+(all\s+)?(previous|above|the)\s+instructions",
            r"(?i)forget\s+(all\s+)?(previous|above|the)\s+instructions",
            r"(?i)override\s+(all\s+)?(previous|above|the)\s+instructions",
            r"(?i)system\s*:",
            r"(?i)assistant\s*:",
            r"(?i)\[INST\]",
            r"(?i)\[/INST\]",
            r"(?i)<<(.*?>>)",
            r"(?i)###\s*(Instruction|Response|System|Assistant)",
        ]

        sanitized = text
        for pattern in injection_patterns:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized)

        # Limit length to prevent DoS
        max_length = 10000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."

        return sanitized

    def _get_mindmap_prompt(
        self,
        note_title: str,
        note_content: str,
        max_levels: int,
    ) -> str:
        """Generate prompt for mindmap creation.

        Args:
            note_title: Note title
            note_content: Note content
            max_levels: Maximum hierarchy levels

        Returns:
            Formatted prompt
        """
        # Sanitize inputs to prevent prompt injection
        safe_title = self._sanitize_for_prompt(note_title)
        safe_content = self._sanitize_for_prompt(note_content)

        return f"""You are an expert at creating structured mind maps from study notes. Analyze the following note and create a hierarchical mind map.

Note Title: {safe_title}

Note Content:
{safe_content}

Requirements:
1. Create a mind map with maximum {max_levels} hierarchy levels
2. Start with the main topic as root
3. Extract key concepts and organize them logically
4. Each node should have a clear, concise label
5. Output MUST be valid JSON only, no additional text

JSON Format:
{{
  "id": "root",
  "text": "Main Topic",
  "children": [
    {{
      "id": "node1",
      "text": "Major Concept 1",
      "children": [
        {{
          "id": "node1-1",
          "text": "Sub-concept 1.1",
          "children": []
        }}
      ]
    }}
  ]
}}

Generate the mind map now:"""

    def _extract_json(self, response: str) -> str:
        """Extract JSON from API response.

        Args:
            response: Raw API response

        Returns:
            Extracted JSON string

        Raises:
            ValueError: If no valid JSON found
        """
        # Try parsing entire response first
        try:
            json.loads(response.strip())
            return response.strip()
        except json.JSONDecodeError:
            pass

        # Try to find JSON within code blocks
        import re

        # Match ```json...``` or ```...```
        pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        match = re.search(pattern, response, re.DOTALL)

        if match:
            return match.group(1)

        # Try to find first { ... } block
        pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        match = re.search(pattern, response, re.DOTALL)

        if match:
            return match.group(0)

        raise ValueError("No valid JSON found in response")

    def _validate_mindmap_structure(
        self,
        structure: Dict[str, Any],
        max_levels: int,
        current_level: int = 1,
    ) -> None:
        """Validate mindmap structure.

        Args:
            structure: Mindmap structure
            max_levels: Maximum allowed levels
            current_level: Current level being validated

        Raises:
            ValueError: If structure is invalid
        """
        required_keys = {"id", "text", "children"}
        if not all(key in structure for key in required_keys):
            raise ValueError(f"Invalid node structure, missing keys: {required_keys}")

        if current_level > max_levels:
            raise ValueError(f"Mindmap exceeds maximum depth of {max_levels}")

        for child in structure.get("children", []):
            self._validate_mindmap_structure(child, max_levels, current_level + 1)

    async def extract_knowledge_points(
        self,
        mindmap_structure: Dict[str, Any],
        node_path: str = "root",
        level: int = 1,
    ) -> List[Dict[str, Any]]:
        """Extract knowledge points from mindmap.

        Args:
            mindmap_structure: Mindmap structure
            node_path: Current node path
            level: Current level

        Returns:
            List of knowledge points
        """
        points = [
            {
                "node_id": mindmap_structure["id"],
                "node_path": node_path,
                "text": mindmap_structure["text"],
                "level": level,
            }
        ]

        for child in mindmap_structure.get("children", []):
            child_path = f"{node_path}/{child['id']}"
            points.extend(
                await self.extract_knowledge_points(child, child_path, level + 1)
            )

        return points
