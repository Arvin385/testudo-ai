"""
Batch-update umd_faculty.csv with courses from Testudo.

- Overwrites ALL existing courses_taught data (full refresh)
- Standardizes all names to "First (Middle) Last" format
- Writes courses as JSON keyed by term: {"Fall 2026": ["CODE: Title", ...]}
- Saves progress every 50 professors so we don't lose work on interruption
"""

import concurrent.futures
import csv
import io
import json
import os
import time
import random
import requests
import sys
import threading
from pathlib import Path

# Fix Windows console encoding for Unicode names (e.g., Romanian ș, accented chars)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Import from our scraper module
sys.path.insert(0, str(Path(__file__).parent))
from scrape_testudo_courses import (
    parse_name, standardize_name, generate_testudo_queries,
    build_search_url, fetch_page, parse_courses,
    HEADERS, DELAY_MIN, DELAY_MAX, DEFAULT_TERMS, TERM_LABELS,
)

CSV_PATH = Path(__file__).parent.parent / "tools" / "umd_faculty.csv"
TERMS = DEFAULT_TERMS  # ["202608"] = Fall 2026
WORKERS = 5            # concurrent HTTP workers; tune to taste

# ---------------------------------------------------------------------------
# Thread-local HTTP sessions (requests.Session is not thread-safe to share)
# ---------------------------------------------------------------------------
_thread_local = threading.local()


def get_session() -> requests.Session:
    if not hasattr(_thread_local, "session"):
        _thread_local.session = requests.Session()
    return _thread_local.session


def format_courses(course_list: list[str], terms: list[str]) -> str:
    """
    Convert course list to JSON keyed by term label.
    e.g. {"Fall 2026": ["CMSC420: Advanced Data Structures", ...]}
    """
    label = TERM_LABELS.get(terms[0], terms[0]) if terms else "Unknown"
    return json.dumps({label: course_list})


def scrape_one(name: str, terms: list[str], session: requests.Session) -> list[str]:
    """Scrape courses for one professor. Returns list of course strings."""
    parsed = parse_name(name)
    queries = generate_testudo_queries(parsed)

    if not queries:
        return []

    all_courses = []
    seen = set()

    for query in queries:
        found_any = False

        for term in terms:
            url = build_search_url(query, term)
            resp = fetch_page(url, session)

            if resp is None:
                continue

            if "No courses matched your search filters" in resp.text:
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                continue

            courses = parse_courses(resp.text)
            if courses:
                found_any = True
                for c in courses:
                    if c not in seen:
                        seen.add(c)
                        all_courses.append(c)

            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        if found_any:
            break

    return all_courses


def save_csv(rows: list[dict], fieldnames: list[str]):
    """Write rows back to CSV."""
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    # Load CSV
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    total = len(rows)

    print(f"Loaded {total} faculty from CSV")
    print(f"  Overwriting all courses_taught data")
    print(f"  Terms: {TERMS}")
    print(f"  Workers: {WORKERS}")
    print(f"  Output format: {{\"Fall 2026\": [\"CODE: Title\", ...]}}")
    print()

    # First pass: standardize ALL names
    names_changed = 0
    for row in rows:
        name = row["Name"].strip()
        if not name or name.startswith("#"):
            continue
        parsed = parse_name(name)
        std = standardize_name(parsed)
        if std != name:
            row["Name"] = std
            names_changed += 1

    print(f"Standardized {names_changed} names to 'First (Middle) Last' format")
    print()

    # Second pass: scrape courses for all faculty (overwrite existing)
    lock = threading.Lock()
    scraped = 0
    found = 0
    not_found = 0
    errors = 0

    processable = [r for r in rows if r["Name"].strip() and not r["Name"].strip().startswith("#")]
    total_to_scrape = len(processable)

    def process_row(row):
        nonlocal scraped, found, not_found, errors
        name = row["Name"].strip()
        dept = row.get("department", "?")
        session = get_session()

        try:
            courses = scrape_one(name, TERMS, session)
        except Exception as e:
            row["courses_taught"] = ""
            with lock:
                errors += 1
                scraped += 1
                print(f"  [{scraped}/{total_to_scrape}] {name} ({dept}) => ERROR: {e}")
                if scraped % 50 == 0:
                    save_csv(rows, fieldnames)
            return

        row["courses_taught"] = format_courses(courses, TERMS) if courses else ""

        with lock:
            if courses:
                found += 1
                status = f"{len(courses)} course(s)"
            else:
                not_found += 1
                status = "none"
            scraped += 1
            print(f"  [{scraped}/{total_to_scrape}] {name} ({dept}) => {status}")

            if scraped % 50 == 0:
                save_csv(rows, fieldnames)
                pct = (found / scraped * 100) if scraped else 0
                print(f"\n  --- Checkpoint: {scraped}/{total_to_scrape} done, "
                      f"{found} found ({pct:.0f}%), saved to CSV ---\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(process_row, row) for row in processable]
        for future in concurrent.futures.as_completed(futures):
            future.result()  # re-raise any unhandled exceptions

    # Final save
    save_csv(rows, fieldnames)

    print()
    print("=" * 60)
    print(f"DONE")
    print(f"  Scraped: {scraped}")
    print(f"  Found courses: {found} ({found/scraped*100:.0f}%)" if scraped else "")
    print(f"  No courses: {not_found}")
    print(f"  Errors: {errors}")
    print(f"  Names standardized: {names_changed}")
    print(f"  CSV saved to: {CSV_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
