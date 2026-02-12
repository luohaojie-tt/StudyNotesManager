"""SQLAlchemy models module"""

# Import all models so they register with SQLAlchemy Base
from app.models.user import User
from app.models.note import Note
from app.models.category import Category, CategoryRelation
from app.models.mindmap import Mindmap, KnowledgePoint
from app.models.quiz import Quiz, QuizQuestion, QuizSession, QuizAnswer
from app.models.mistake import Mistake, MistakeReview
from app.models.share import NoteShare, StudySession

__all__ = [
    "User",
    "Note",
    "Category",
    "CategoryRelation",
    "Mindmap",
    "KnowledgePoint",
    "Quiz",
    "QuizQuestion",
    "QuizSession",
    "QuizAnswer",
    "Mistake",
    "MistakeReview",
    "NoteShare",
    "StudySession",
]
