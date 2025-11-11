"""Tool: get_courses_for_term — list a user's courses for a specific term.

Inputs
- uid (str, required): User ID.
- term (str, required): Term key 'YYYY-MM'.

Returns (JSON)
- Success:
  {"status":"success","userId": uid,"term": term,"courses":[{...}], "meta":{"count": N}}
- Not found (user or term):
  {"status":"not_found","userId": uid,"term": term}
- Error:
  {"status":"error","message":"..."}
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from pymongo.errors import PyMongoError

from .mongo_client import MongoDBError, get_collection

_TERM_RE = re.compile(r"^\d{4}-\d{2}$")


def get_courses_for_term(*, uid: str, term: str) -> Dict[str, Any]:
    """Return the user's course list for a given term or not_found if empty."""

    if not uid or not isinstance(uid, str):
        return {"status": "error", "message": "uid must be a non-empty string"}
    if not term or not isinstance(term, str) or not _TERM_RE.match(term):
        return {"status": "error", "message": "term must be 'YYYY-MM'"}

    try:
        doc = get_collection().find_one({"_id": uid}, {f"courses.{term}": 1})
        courses: List[Dict[str, Any]] = (doc or {}).get("courses", {}).get(term, [])  # type: ignore[assignment]
        if not courses:
            return {"status": "not_found", "userId": uid, "term": term}
        return {
            "status": "success",
            "userId": uid,
            "term": term,
            "courses": courses,
            "meta": {"count": len(courses)},
        }
    except (MongoDBError, PyMongoError) as exc:
        return {"status": "error", "message": str(exc)}
