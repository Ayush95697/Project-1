from typing import Any, Dict, List, Optional

from pymongo.database import Database

from app.db import get_database
from app.models.question import Question


def _questions_collection(db: Database):
    return db["questions"]


def get_all_questions(db: Database | None = None) -> List[Dict[str, Any]]:
    if db is None:
        db = get_database()
    coll = _questions_collection(db)
    return list(coll.find({}))


def get_question_by_id(question_id: str, db: Database | None = None) -> Optional[Dict[str, Any]]:
    if db is None:
        db = get_database()
    coll = _questions_collection(db)
    return coll.find_one({"_id": question_id})


def sanitize_question_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive fields like correct_answer before returning to clients.
    """
    if not doc:
        return doc
    return {
        "question_id": doc["_id"],
        "question_text": doc["question_text"],
        "options": doc["options"],
        "difficulty": float(doc["difficulty"]),
        "topic": doc["topic"],
    }

