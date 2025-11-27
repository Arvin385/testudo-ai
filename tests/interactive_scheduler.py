"""Interactive tester for scheduler get_*.py tools.

Run:
  python tests/interactive_scheduler.py

This script prompts for inputs and calls the scheduler helpers in `scheduler/`.
It also ensures the project root is on sys.path so imports resolve when run from
an editor or different working directory.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any, Optional

# Ensure the project root is on sys.path when running this file directly.
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scheduler.get_course_by_code import get_course_by_code
from scheduler.get_courses_by_filters import get_courses_by_filters
from scheduler.get_department_list import get_department_list
from scheduler.get_instructor_info import get_instructor_info
from scheduler.get_sections_by_course_code import get_sections_by_course_code


def jprint(obj: Any) -> None:
    print(json.dumps(obj, indent=2, default=str))


def input_nonempty(prompt: str) -> str:
    while True:
        val = input(prompt).strip()
        if val:
            return val
        print("Please enter a non-empty value.")


def to_bool_yesno(s: str) -> bool:
    return s.strip().lower() in ("y", "yes", "1", "true")


def menu() -> None:
    print("Interactive scheduler tester")
    print("Calls JupiterP-backed scheduler helpers from the `scheduler/` package.")
    print()

    while True:
        print("\nSelect an action:")
        print("  1) get_course_by_code")
        print("  2) get_courses_by_filters")
        print("  3) get_sections_by_course_code")
        print("  4) get_instructor_info")
        print("  5) get_department_list")
        print("  6) quit")

        choice = input("Enter number: ").strip()
        if choice == "1":
            code = input_nonempty("Course code (e.g. CMSC131): ")
            inc = input("Include sections? (y/N): ").strip()
            base = input("Base URL override (optional): ").strip() or None
            try:
                timeout = float(input("Timeout seconds (default 10): ").strip() or 10)
            except ValueError:
                timeout = 10.0
            jprint(
                get_course_by_code(
                    code,
                    include_sections=to_bool_yesno(inc),
                    base_url=base,
                    timeout=timeout,
                )
            )

        elif choice == "2":
            codes = (
                input("Course codes (comma-separated) or leave blank: ").strip() or None
            )
            prefix = input("Prefix (e.g. CMSC) or leave blank: ").strip() or None
            gen_ed = input("Gen-ed code (e.g. QR) or leave blank: ").strip() or None
            page = input("Page number (optional): ").strip() or None
            per_page = input("Per-page (optional): ").strip() or None
            base = input("Base URL override (optional): ").strip() or None
            params = {}
            if codes:
                params["courseCodes"] = ",".join(
                    [c.strip().upper() for c in codes.split(",") if c.strip()]
                )
            if prefix:
                params["prefix"] = prefix
            if gen_ed:
                params["genEds"] = gen_ed
            if page:
                try:
                    params["page"] = int(page)
                except ValueError:
                    pass
            if per_page:
                try:
                    params["perPage"] = int(per_page)
                except ValueError:
                    pass
            jprint(get_courses_by_filters(base_url=base, timeout=10.0, **params))

        elif choice == "3":
            codes = input_nonempty("Course codes (comma-separated) or single code: ")
            only_open = input("Only open sections? (y/N): ").strip()
            instructor = input("Instructor name (optional): ").strip() or None
            base = input("Base URL override (optional): ").strip() or None
            params = {
                "courseCodes": ",".join(
                    [c.strip().upper() for c in codes.split(",") if c.strip()]
                )
            }
            if instructor:
                params["instructorName"] = instructor
            jprint(
                get_sections_by_course_code(
                    base_url=base,
                    timeout=10.0,
                    only_open=to_bool_yesno(only_open),
                    **params,
                )
            )

        elif choice == "4":
            name = (
                input("Instructor name (leave blank for active list): ").strip() or None
            )
            active_only = input("Active only? (Y/n): ").strip()
            base = input("Base URL override (optional): ").strip() or None
            if name:
                jprint(get_instructor_info(name=name, base_url=base))
            else:
                jprint(
                    get_instructor_info(
                        active_only=to_bool_yesno(active_only), base_url=base
                    )
                )

        elif choice == "5":
            jprint(get_department_list())

        elif choice == "6":
            print("Goodbye")
            break

        else:
            print("Unknown choice; please enter 1-6")


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        sys.exit(0)
