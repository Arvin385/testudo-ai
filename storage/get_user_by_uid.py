"""Tool: get_user_by_uid — fetch a user's document by UID.

Inputs
- uid (str, required): The user's unique ID.
- fields (list[str], optional): Whitelist projection of fields to include.

Returns (JSON)
- Success:
  {"status":"success","user":{"_id": "...", ...}}
- Not found:
  {"status":"not_found","userId": uid}
- Error:
  {"status":"error","message":"..."}
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pymongo.errors import PyMongoError

from .mongo_client import MongoDBError, get_collection


def get_user_by_uid(*, uid: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Fetch a user document by _id with optional projection."""

    if not uid or not isinstance(uid, str):
        return {"status": "error", "message": "uid must be a non-empty string"}

    projection: Optional[Dict[str, int]] = None
    if fields:
        projection = {k: 1 for k in fields}
        projection["_id"] = 1

    try:
        doc = get_collection().find_one({"_id": uid}, projection)
        if not doc:
            return {"status": "not_found", "userId": uid}
        return {"status": "success", "user": doc}
    except (MongoDBError, PyMongoError) as exc:
        return {"status": "error", "message": str(exc)}
