import logging
from typing import Any

from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.utils.settings import get_settings

logger = logging.getLogger(__name__)

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is not None:
        return _client

    settings = get_settings()
    try:
        _client = MongoClient(settings.mongodb_uri)
        # Trigger a simple command to validate connection early.
        _client.admin.command("ping")
        return _client
    except PyMongoError as exc:
        logger.exception("Failed to connect to MongoDB")
        raise RuntimeError("Database connection failure") from exc


def get_database() -> Database:
    settings = get_settings()
    client = get_client()
    db = client[settings.mongodb_db_name]

    # Ensure required indexes exist.
    try:
        questions: Collection[Any] = db["questions"]
        questions.create_index([("difficulty", ASCENDING)])
        questions.create_index([("_id", ASCENDING)], unique=True)

        sessions: Collection[Any] = db["user_sessions"]
        sessions.create_index([("_id", ASCENDING)], unique=True)
        sessions.create_index([("status", ASCENDING)])
    except PyMongoError as exc:
        logger.exception("Failed to create indexes")
        raise RuntimeError("Database index creation failure") from exc

    return db

