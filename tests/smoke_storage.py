"""Quick smoke test for storage tools against a MongoDB Atlas cluster.

Requires environment variable MONGODB_URI to be set. Optionally set
MONGODB_DB (default: 'userdata') and MONGODB_USERS_COLL (default: 'users').

This script exercises:
- ping
- ensure_user_indexes
- upsert_user_profile
- add_course_for_term
- get_courses_for_term
- get_user_by_uid
- remove_course_for_term
"""

from __future__ import annotations

import json
from uuid import uuid4

from storage.add_course_for_term import add_course_for_term
from storage.ensure_user_indexes import ensure_user_indexes
from storage.get_courses_for_term import get_courses_for_term
from storage.get_user_by_uid import get_user_by_uid
from storage.mongo_client import ping
from storage.remove_course_for_term import remove_course_for_term
from storage.upsert_user_profile import upsert_user_profile


def pfx(title: str) -> None:
    print("\n===", title, "===")


def pretty(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def main() -> None:
    uid = f"smoke_{uuid4().hex[:8]}"
    term = "2025-03"

    pfx("ping")
    pretty(ping())

    pfx("ensure_user_indexes")
    pretty(ensure_user_indexes())

    pfx("upsert_user_profile")
    pretty(upsert_user_profile(uid=uid, name="Smoke User"))

    pfx("add_course_for_term")
    pretty(
        add_course_for_term(
            uid=uid,
            term=term,
            course={
                "name": "Object-Oriented Programming I",
                "code": "CMSC131",
                "section": "0101",
                "credits": 4,
            },
        )
    )

    pfx("get_courses_for_term")
    pretty(get_courses_for_term(uid=uid, term=term))

    pfx("get_user_by_uid")
    pretty(get_user_by_uid(uid=uid))

    pfx("remove_course_for_term")
    pretty(remove_course_for_term(uid=uid, term=term, code="CMSC131", section="0101"))


if __name__ == "__main__":
    main()
