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
from typing import Any, Dict, List, Optional

from pymongo.errors import PyMongoError

from .mongo_client import MongoDBError, get_collection


def upsert_user_profile(
    *,
    uid: str,
    name: Optional[str] = None,
    directory_id: Optional[str] = None,
    friends_outgoing: Optional[List[str]] = None,
    friends_incoming: Optional[List[str]] = None,
    friends: Optional[List[str]] = None,
    courses: Optional[Dict[str, Dict[str, Any]]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create or update a user profile using uid as the document _id."""

    if not uid or not isinstance(uid, str):
        return {"status": "error", "message": "uid must be a non-empty string"}

    updates: Dict[str, Any] = {
        "$setOnInsert": {"date_added": datetime.now(timezone.utc)}
    }

    # Collect all the fields we might want to update
    set_fields: Dict[str, Any] = {}

    if name is not None:
        set_fields["name"] = name
    if directory_id is not None:
        set_fields["directory_id"] = directory_id
    if friends_outgoing is not None:
        set_fields["friends_outgoing"] = friends_outgoing
    if friends_incoming is not None:
        set_fields["friends_incoming"] = friends_incoming
    if friends is not None:
        set_fields["friends"] = friends
    if courses is not None:
        set_fields["courses"] = courses
    if extra:
        set_fields.update(extra)

    # Only include $set if there’s something to set
    if set_fields:
        updates["$set"] = set_fields

    try:
        coll = get_collection()
        result = coll.update_one({"_id": uid}, updates, upsert=True)
        return {
            "status": "success",
            "userId": uid,
            "upserted": bool(result.upserted_id),
            "modified": int(result.modified_count),
        }
    except (MongoDBError, PyMongoError) as exc:
        return {"status": "error", "message": str(exc)}
