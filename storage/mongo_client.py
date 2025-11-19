"""Shared MongoDB client utilities for Atlas (M0) and the 'userdata.users' collection.

Environment
- MONGODB_URI: Atlas connection string (required in production).
- MONGODB_DB: Database name; defaults to 'userdata'.
- MONGODB_USERS_COLL: Collection name; defaults to 'users'.

Functions
- get_collection(db_name?, coll_name?): returns a pymongo Collection (users by default).
- ensure_indexes(): creates helpful indexes for the users collection.
- ping(): health check, returns a JSON-style dict result.

Errors
- MongoDBError: wrapper for pymongo errors and connectivity issues.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()


from pymongo import ASCENDING, MongoClient, errors
from pymongo.collection import Collection


class MongoDBError(Exception):
    """Raised for MongoDB configuration or connectivity failures."""


_client: Optional[MongoClient] = None


def _db_name() -> str:
    return os.environ.get("MONGODB_DB", "userdata")


def _users_coll_name() -> str:
    return os.environ.get("MONGODB_USERS_COLL", "users")


def _get_uri() -> str:
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise MongoDBError("MONGODB_URI is not set")
    return uri


def get_client() -> MongoClient:
    """Return a cached MongoClient configured for Atlas."""

    global _client
    if _client is None:
        try:
            _client = MongoClient(_get_uri(), tls=True, serverSelectionTimeoutMS=5000)
        except errors.PyMongoError as exc:
            raise MongoDBError(str(exc)) from exc
    return _client


def get_collection(
    db_name: Optional[str] = None, coll_name: Optional[str] = None
) -> Collection:
    """Get a collection handle (defaults to users collection)."""

    try:
        client = get_client()
        db = client[db_name or _db_name()]
        return db[coll_name or _users_coll_name()]
    except errors.PyMongoError as exc:
        raise MongoDBError(str(exc)) from exc


def ensure_indexes() -> Dict[str, Any]:
    """Create recommended indexes for the users collection and return JSON-style result."""

    try:
        coll = get_collection()
        created = []
        created.append(
            coll.create_index([("dateAdded", ASCENDING)], name="idx_dateAdded")
        )
        return {"status": "success", "created": created}
    except (errors.PyMongoError, MongoDBError) as exc:
        return {"status": "error", "message": str(exc)}


def ping() -> Dict[str, Any]:
    """Return a JSON-style health check result for MongoDB connectivity."""

    try:
        get_client().admin.command("ping")
        return {"status": "success"}
    except errors.PyMongoError as exc:
        return {"status": "error", "message": str(exc)}
