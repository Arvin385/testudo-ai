"""Tool: add_course_for_term — append a course to a user's term course list.

Inputs
- uid (str, required): User ID.
- term (str, required): Term key 'YYYY-MM' (e.g., '2025-03' for Fall 2025).
- course (dict, required): { "name": str, "code": str, "section": str, "credits": number }

Behavior
- Normalizes code to uppercase, section to string, credits to float.
- Creates the user doc with dateAdded if it doesn't exist.
- Uses $addToSet to avoid inserting exact duplicates.

Returns (JSON)
- Success:
  {"status":"success","userId": uid,"term": term,"added": bool}
- Validation error:
  {"status":"error","message":"..."}
- Mongo error:
  {"status":"error","message":"..."}
"""

from __future__ import annotations

import re
from typing import Any, Dict

from pymongo.errors import PyMongoError

from .mongo_client import MongoDBError, get_collection

_TERM_RE = re.compile(r"^\d{4}-\d{2}$")


def add_course_for_term(
    *, uid: str, term: str, course: Dict[str, Any]
) -> Dict[str, Any]:
    """Add or deduplicate a course item within a user's term array."""

    if not uid or not isinstance(uid, str):
        return {"status": "error", "message": "uid must be a non-empty string"}
    if not term or not isinstance(term, str) or not _TERM_RE.match(term):
        return {
            "status": "error",
            "message": "term must be 'YYYY-MM' (e.g., '2025-03')",
        }
    if not isinstance(course, dict):
        return {"status": "error", "message": "course must be an object"}

    doc = {
        "name": str(course.get("name", "")).strip(),
        "code": str(course.get("code", "")).upper().strip(),
        "section": str(course.get("section", "")).strip(),
        "credits": float(course.get("credits", 0) or 0),
    }
    if not doc["code"]:
        return {"status": "error", "message": "course.code is required"}

    try:
        coll = get_collection()
        res = coll.update_one(
            {"_id": uid},
            {
                "$setOnInsert": {"dateAdded": __import__("datetime").datetime.utcnow()},
                "$addToSet": {f"courses.{term}": doc},
            },
            upsert=True,
        )
        return {
            "status": "success",
            "userId": uid,
            "term": term,
            "added": bool(res.modified_count),
        }
    except (MongoDBError, PyMongoError) as exc:
        return {"status": "error", "message": str(exc)}
