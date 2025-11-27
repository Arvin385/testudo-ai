"""Interactive tester for storage tools using input() prompts.

Run:
  python tests/interactive_storage.py

The script shows a small menu. It requires MONGODB_URI to be set (or a .env
with MONGODB_URI if you've set up dotenv). It will call the same functions in
`storage` and print JSON responses.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from typing import Any

# Ensure the project root is on sys.path when running this file directly.
# This helps avoid "ModuleNotFoundError: No module named 'storage'"
# when the current working directory isn't the repository root (e.g. running
# from an editor, tests runner, or other subdirectory).
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storage.add_course_for_term import add_course_for_term
from storage.get_courses_for_term import get_courses_for_term
from storage.get_user_by_uid import get_user_by_uid
from storage.mongo_client import ensure_indexes, ping
from storage.remove_course_for_term import remove_course_for_term
from storage.upsert_user_profile import upsert_user_profile


def jprint(obj: Any) -> None:
    print(json.dumps(obj, indent=2, default=str))


def input_nonempty(prompt: str) -> str:
    while True:
        val = input(prompt).strip()
        if val:
            return val
        print("Please enter a non-empty value.")


def menu() -> None:
    print("Interactive storage tester")
    print(
        "Ensure MONGODB_URI is set in your environment (or use a .env file if configured)."
    )
    print()

    while True:
        print("\nSelect an action:")
        print("  1) ping")
        print("  2) ensure_indexes")
        print("  3) upsert_user")
        print("  4) add_course")
        print("  5) list_courses")
        print("  6) get_user")
        print("  7) remove_course")
        print("  8) quit")

        choice = input("Enter number: ").strip()
        if choice == "1":
            jprint(ping())

        elif choice == "2":
            jprint(ensure_indexes())

        elif choice == "3":
            uid = input_nonempty("User id (uid): ")
            name = input("Display name (optional): ").strip() or None
            res = upsert_user_profile(uid=uid, name=name)
            jprint(res)

        elif choice == "4":
            uid = input_nonempty("User id (uid): ")
            term = input_nonempty("Term (YYYY-MM): ")
            code = input_nonempty("Course code (e.g. CMSC131): ")
            section = input("Section (optional): ").strip()
            name = input("Course name (optional): ").strip() or code
            credits_raw = input("Credits (optional, number): ").strip()
            try:
                credits = float(credits_raw) if credits_raw else 0
            except ValueError:
                print("Invalid credits; using 0")
                credits = 0
            course = {
                "name": name,
                "code": code,
                "section": section,
                "credits": credits,
            }
            jprint(add_course_for_term(uid=uid, term=term, course=course))

        elif choice == "5":
            uid = input_nonempty("User id (uid): ")
            term = input_nonempty("Term (YYYY-MM): ")
            jprint(get_courses_for_term(uid=uid, term=term))

        elif choice == "6":
            uid = input_nonempty("User id (uid): ")
            jprint(get_user_by_uid(uid=uid))

        elif choice == "7":
            uid = input_nonempty("User id (uid): ")
            term = input_nonempty("Term (YYYY-MM): ")
            code = input_nonempty("Course code to remove: ")
            section = input("Section (optional to narrow removal): ").strip() or None
            jprint(
                remove_course_for_term(uid=uid, term=term, code=code, section=section)
            )

        elif choice == "8":
            print("Goodbye")
            break

        else:
            print("Unknown choice; please enter 1-8")


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        sys.exit(0)
