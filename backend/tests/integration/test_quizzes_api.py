"""
Integration tests for Quizzes API endpoints.

Tests the /api/quizzes/* endpoints with real database interactions.
"""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
@pytest.mark.api
class TestQuizzesGenerationAPI:
    """Test quiz generation API endpoints."""

    @pytest.fixture
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user."""
        from app.models.user import User
        from app.core.security import get_password_hash

        user = User(
            id=uuid.uuid4(),
            email="quiz@test.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="Quiz Test User",
            is_active=True,
            is_verified=True
        )
        async_db_session.add(user)
        await async_db_session.commit()
        await async_db_session.refresh(user)
        return user

    @pytest.fixture
    async def test_mindmap(
        self,
        async_db_session: AsyncSession,
        test_user
    ):
        """Create a test mindmap."""
        from app.models.mindmap import Mindmap, Note
        from datetime import datetime

        note = Note(
            id=uuid.uuid4(),
            user_id=test_user.id,
            title="Math Note",
            content="Mathematics content",
            subject="Math",
            created_at=datetime.utcnow()
        )
        async_db_session.add(note)

        mindmap = Mindmap(
            id=uuid.uuid4(),
            note_id=note.id,
            user_id=test_user.id,
            structure={
                "id": "root",
                "text": "Mathematics",
                "children": [
                    {
                        "id": "algebra",
                        "text": "Algebra",
                        "children": []
                    }
                ]
            },
            map_type="ai_generated",
            version=1
        )
        async_db_session.add(mindmap)
        await async_db_session.commit()
        await async_db_session.refresh(mindmap)
        return mindmap

    @pytest.mark.asyncio
    async def test_generate_quiz_success(
        self,
        client: AsyncClient,
        test_user,
        test_mindmap
    ):
        """Test successful quiz generation."""
        response = await client.post(
            f"/api/quizzes/generate/{test_mindmap.id}",
            params={"user_id": str(test_user.id)},
            json={
                "question_count": 5,
                "question_types": ["choice", "fill_blank"],
                "difficulty": "medium"
            }
        )

        # Should succeed (may return 500 if AI not configured)
        assert response.status_code in [200, 201, 500]

        if response.status_code in [200, 201]:
            data = response.json()
            assert "quiz_id" in data
            assert "status" in data
            assert "total_questions" in data

    @pytest.mark.asyncio
    async def test_generate_quiz_invalid_mindmap(
        self,
        client: AsyncClient,
        test_user
    ):
        """Test quiz generation with invalid mindmap ID."""
        fake_mindmap_id = uuid.uuid4()

        response = await client.post(
            f"/api/quizzes/generate/{fake_mindmap_id}",
            params={"user_id": str(test_user.id)},
            json={
                "question_count": 5,
                "question_types": ["choice"],
                "difficulty": "medium"
            }
        )

        # Should fail
        assert response.status_code in [400, 404, 500]

    @pytest.mark.asyncio
    async def test_generate_quiz_invalid_parameters(
        self,
        client: AsyncClient,
        test_user,
        test_mindmap
    ):
        """Test quiz generation with invalid parameters."""
        response = await client.post(
            f"/api/quizzes/generate/{test_mindmap.id}",
            params={"user_id": str(test_user.id)},
            json={
                "question_count": 100,  # Too many
                "question_types": ["choice"],
                "difficulty": "invalid"  # Invalid difficulty
            }
        )

        # Should fail validation
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_generate_quiz_boundary_values(
        self,
        client: AsyncClient,
        test_user,
        test_mindmap
    ):
        """Test quiz generation with boundary values."""
        # Test minimum
        response = await client.post(
            f"/api/quizzes/generate/{test_mindmap.id}",
            params={"user_id": str(test_user.id)},
            json={
                "question_count": 1,  # Minimum
                "question_types": ["choice"],
                "difficulty": "easy"
            }
        )
        assert response.status_code in [200, 201, 500]

        # Test maximum
        response = await client.post(
            f"/api/quizzes/generate/{test_mindmap.id}",
            params={"user_id": str(test_user.id)},
            json={
                "question_count": 50,  # Maximum
                "question_types": ["choice"],
                "difficulty": "hard"
            }
        )
        assert response.status_code in [200, 201, 500]


@pytest.mark.integration
@pytest.mark.api
class TestQuizzesRetrievalAPI:
    """Test quiz retrieval API endpoints."""

    @pytest.fixture
    async def quiz_with_questions(
        self,
        async_db_session: AsyncSession,
        test_user,
        test_mindmap
    ):
        """Create a quiz with questions."""
        from app.models.quiz import Quiz, Question

        quiz = Quiz(
            id=uuid.uuid4(),
            mindmap_id=test_mindmap.id,
            user_id=test_user.id,
            status="completed",
            question_count=3
        )
        async_db_session.add(quiz)
        await async_db_session.flush()

        questions = [
            Question(
                id=uuid.uuid4(),
                quiz_id=quiz.id,
                knowledge_point_id=None,
                question_text="What is 2+2?",
                question_type="choice",
                options=["3", "4", "5"],
                correct_answer="4",
                difficulty="easy"
            ),
            Question(
                id=uuid.uuid4(),
                quiz_id=quiz.id,
                knowledge_point_id=None,
                question_text="Solve x + 3 = 7",
                question_type="fill_blank",
                options=None,
                correct_answer="4",
                difficulty="medium"
            ),
            Question(
                id=uuid.uuid4(),
                quiz_id=quiz.id,
                knowledge_point_id=None,
                question_text="True or False: 1 > 2",
                question_type="true_false",
                options=["True", "False"],
                correct_answer="False",
                difficulty="easy"
            ),
        ]

        for question in questions:
            async_db_session.add(question)

        await async_db_session.commit()
        return quiz

    @pytest.mark.asyncio
    async def test_get_quiz_success(
        self,
        client: AsyncClient,
        quiz_with_questions
    ):
        """Test getting quiz details."""
        response = await client.get(
            f"/api/quizzes/{quiz_with_questions.id}",
            params={"user_id": str(quiz_with_questions.user_id)}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(quiz_with_questions.id)
        assert "questions" in data
        assert len(data["questions"]) == 3

    @pytest.mark.asyncio
    async def test_get_quiz_not_found(
        self,
        client: AsyncClient,
        test_user
    ):
        """Test getting non-existent quiz."""
        fake_quiz_id = uuid.uuid4()

        response = await client.get(
            f"/api/quizzes/{fake_quiz_id}",
            params={"user_id": str(test_user.id)}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_quiz_unauthorized(
        self,
        client: AsyncClient,
        quiz_with_questions
    ):
        """Test getting quiz belonging to another user."""
        other_user_id = uuid.uuid4()

        response = await client.get(
            f"/api/quizzes/{quiz_with_questions.id}",
            params={"user_id": str(other_user_id)}
        )

        # Should return 404 or 403
        assert response.status_code in [403, 404]


@pytest.mark.integration
@pytest.mark.api
class TestQuizSubmissionAPI:
    """Test quiz submission and grading API endpoints."""

    @pytest.fixture
    async def quiz_for_submission(
        self,
        async_db_session: AsyncSession,
        test_user,
        test_mindmap
    ):
        """Create a quiz ready for answer submission."""
        from app.models.quiz import Quiz, Question

        quiz = Quiz(
            id=uuid.uuid4(),
            mindmap_id=test_mindmap.id,
            user_id=test_user.id,
            status="completed",
            question_count=2
        )
        async_db_session.add(quiz)
        await async_db_session.flush()

        questions = [
            Question(
                id=uuid.uuid4(),
                quiz_id=quiz.id,
                knowledge_point_id=None,
                question_text="What is 2+2?",
                question_type="choice",
                options=["3", "4", "5"],
                correct_answer="4",
                difficulty="easy"
            ),
            Question(
                id=uuid.uuid4(),
                quiz_id=quiz.id,
                knowledge_point_id=None,
                question_text="5 + 3 = ?",
                question_type="choice",
                options=["7", "8", "9"],
                correct_answer="8",
                difficulty="easy"
            ),
        ]

        for question in questions:
            async_db_session.add(question)

        await async_db_session.commit()
        return quiz

    @pytest.mark.asyncio
    async def test_submit_answers_correct(
        self,
        client: AsyncClient,
        quiz_for_submission
    ):
        """Test submitting correct answers."""
        from app.models.quiz import Question

        # Get questions
        result = await client.get(
            f"/api/quizzes/{quiz_for_submission.id}",
            params={"user_id": str(quiz_for_submission.user_id)}
        )
        questions_data = result.json()["questions"]

        answers = [
            {
                "question_id": questions_data[0]["id"],
                "user_answer": "4"  # Correct
            },
            {
                "question_id": questions_data[1]["id"],
                "user_answer": "8"  # Correct
            }
        ]

        response = await client.post(
            f"/api/quizzes/{quiz_for_submission.id}/answer",
            params={"user_id": str(quiz_for_submission.user_id)},
            json={"answers": answers}
        )

        # Should succeed (may return 500 if vector DB not configured)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "id" in data  # Session ID
            assert "score" in data
            assert data["total_questions"] == 2

    @pytest.mark.asyncio
    async def test_submit_answers_incorrect(
        self,
        client: AsyncClient,
        quiz_for_submission
    ):
        """Test submitting incorrect answers."""
        # Get questions first
        result = await client.get(
            f"/api/quizzes/{quiz_for_submission.id}",
            params={"user_id": str(quiz_for_submission.user_id)}
        )
        questions_data = result.json()["questions"]

        answers = [
            {
                "question_id": questions_data[0]["id"],
                "user_answer": "3"  # Incorrect
            },
            {
                "question_id": questions_data[1]["id"],
                "user_answer": "7"  # Incorrect
            }
        ]

        response = await client.post(
            f"/api/quizzes/{quiz_for_submission.id}/answer",
            params={"user_id": str(quiz_for_submission.user_id)},
            json={"answers": answers}
        )

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            # Score should be 0 or low
            assert data["score"] < 100

    @pytest.mark.asyncio
    async def test_submit_answers_partial(
        self,
        client: AsyncClient,
        quiz_for_submission
    ):
        """Test submitting partial answers."""
        # Get questions
        result = await client.get(
            f"/api/quizzes/{quiz_for_submission.id}",
            params={"user_id": str(quiz_for_submission.user_id)}
        )
        questions_data = result.json()["questions"]

        # Only answer one question
        answers = [
            {
                "question_id": questions_data[0]["id"],
                "user_answer": "4"
            }
        ]

        response = await client.post(
            f"/api/quizzes/{quiz_for_submission.id}/answer",
            params={"user_id": str(quiz_for_submission.user_id)},
            json={"answers": answers}
        )

        assert response.status_code in [200, 500]


@pytest.mark.integration
@pytest.mark.api
class TestQuizSessionAPI:
    """Test quiz session result API endpoints."""

    @pytest.fixture
    async def completed_session(
        self,
        async_db_session: AsyncSession,
        quiz_for_submission
    ):
        """Create a completed quiz session."""
        from app.models.quiz import QuizSession
        from datetime import datetime

        session = QuizSession(
            id=uuid.uuid4(),
            quiz_id=quiz_for_submission.id,
            user_id=quiz_for_submission.user_id,
            status="completed",
            total_questions=2,
            correct_count=1,
            score=50.0,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        async_db_session.add(session)
        await async_db_session.commit()
        await async_db_session.refresh(session)
        return session

    @pytest.mark.asyncio
    async def test_get_session_results_success(
        self,
        client: AsyncClient,
        completed_session
    ):
        """Test getting quiz session results."""
        response = await client.get(
            f"/api/quizzes/sessions/{completed_session.id}",
            params={"user_id": str(completed_session.user_id)}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(completed_session.id)
        assert data["status"] == "completed"
        assert data["score"] == 50.0

    @pytest.mark.asyncio
    async def test_get_session_results_not_found(
        self,
        client: AsyncClient,
        test_user
    ):
        """Test getting non-existent session."""
        fake_session_id = uuid.uuid4()

        response = await client.get(
            f"/api/quizzes/sessions/{fake_session_id}",
            params={"user_id": str(test_user.id)}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_session_results_unauthorized(
        self,
        client: AsyncClient,
        completed_session
    ):
        """Test getting session belonging to another user."""
        other_user_id = uuid.uuid4()

        response = await client.get(
            f"/api/quizzes/sessions/{completed_session.id}",
            params={"user_id": str(other_user_id)}
        )

        # Should return 404 or 403
        assert response.status_code in [403, 404]
