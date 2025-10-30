"""Tool: upsert_user_profile — create or update a user's profile document.

Inputs
- uid (str, required): The user's unique ID; stored as _id.
- name (str, optional): Display name.
- extra (dict, optional): Arbitrary profile fields to set/overwrite.

Behavior
- If the user does not exist, inserts with _id=uid and dateAdded (UTC).
- If the user exists, updates provided fields only.

Returns (JSON)
- Success:
  {"status":"success","userId": uid, "upserted": bool, "modified": int}
- Error:
  {"status":"error","message":"..."}
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pymongo.errors import PyMongoError

from .mongo_client import MongoDBError, get_collection


def upsert_user_profile(
    *, uid: str, name: Optional[str] = None, extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create or update a user profile using uid as the document _id."""

    if not uid or not isinstance(uid, str):
        return {"status": "error", "message": "uid must be a non-empty string"}

    updates: Dict[str, Any] = {
        "$setOnInsert": {"dateAdded": datetime.now(timezone.utc)}
    }
    if name is not None:
        updates.setdefault("$set", {})["name"] = name
    if extra:
        updates.setdefault("$set", {}).update(extra)

    try:
        coll = get_collection()
        result = coll.update_one({"_id": uid}, updates, upsert=True)
        upserted = result.upserted_id is not None
        modified = result.modified_count
        return {
            "status": "success",
            "userId": uid,
            "upserted": bool(upserted),
            "modified": int(modified),
        }
    except (MongoDBError, PyMongoError) as exc:
        return {"status": "error", "message": str(exc)}
