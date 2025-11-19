"""Tool: remove_course_for_term — remove a course from a user's term.

Inputs
- uid (str, required): User ID.
- term (str, required): Term key 'YYYY-MM'.
- code (str, required): Course code (e.g., 'CMSC131'); case-insensitive.
- section (str, optional): If provided, only remove matching section.

Returns (JSON)
- Success:
  {"status":"success","userId": uid,"term": term,"removed": N}
- Not found (no match removed):
  {"status":"not_found","userId": uid,"term": term}
- Error:
  {"status":"error","message":"..."}
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from pymongo.errors import PyMongoError

from .mongo_client import MongoDBError, get_collection

_TERM_RE = re.compile(r"^\d{4}-\d{2}$")


def remove_course_for_term(
    *, uid: str, term: str, code: str, section: Optional[str] = None
) -> Dict[str, Any]:
    """Remove matching course entries from the user's term course list."""

    if not uid or not isinstance(uid, str):
        return {"status": "error", "message": "uid must be a non-empty string"}
    if not term or not isinstance(term, str) or not _TERM_RE.match(term):
        return {"status": "error", "message": "term must be 'YYYY-MM'"}
    if not code:
        return {"status": "error", "message": "code is required"}

    match: Dict[str, Any] = {"code": str(code).upper()}
    if section is not None:
        match["section"] = str(section)

    try:
        res = get_collection().update_one(
            {"_id": uid}, {"$pull": {f"courses.{term}": match}}
        )
        if res.modified_count == 0:
            return {"status": "not_found", "userId": uid, "term": term}
        return {
            "status": "success",
            "userId": uid,
            "term": term,
            "removed": int(res.modified_count),
        }
    except (MongoDBError, PyMongoError) as exc:
        return {"status": "error", "message": str(exc)}
