"""
Batch-update umd_faculty.csv with courses from Testudo.

- Skips professors who already have courses_taught data
- Standardizes all names to "First (Middle) Last" format
- Writes courses in format: "CODE1:Title1; CODE2:Title2; ..."
- Saves progress every 50 professors so we don't lose work on interruption
"""

import csv
import io
import os
import time
import random
import requests
import sys
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
    HEADERS, DELAY_MIN, DELAY_MAX, DEFAULT_TERMS,
)

CSV_PATH = Path(__file__).parent.parent / "tools" / "umd_faculty.csv"
TERMS = DEFAULT_TERMS  # ["202601", "202508"]


def format_courses(course_list: list[str]) -> str:
    """
    Convert ["CMSC216: Introduction to Computer Systems", ...]
    to "CMSC216:Introduction to Computer Systems; ..."
    """
    # parse_courses returns "CODE: Title", we want "CODE:Title"
    formatted = []
    for c in course_list:
        # Split on first ": " to get code and title
        if ": " in c:
            code, title = c.split(": ", 1)
            formatted.append(f"{code}:{title}")
        else:
            formatted.append(c)
    return "; ".join(formatted)


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
    needs_scraping = sum(1 for r in rows if not r.get("courses_taught", "").strip())
    already_has = total - needs_scraping

    print(f"Loaded {total} faculty from CSV")
    print(f"  Already have courses_taught: {already_has} (skipping)")
    print(f"  Need scraping: {needs_scraping}")
    print(f"  Terms: {TERMS}")
    print(f"  Output format: CODE:Title; CODE:Title; ...")
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

    # Second pass: scrape courses for those missing them
    session = requests.Session()
    scraped = 0
    found = 0
    not_found = 0
    errors = 0

    for i, row in enumerate(rows):
        name = row["Name"].strip()

        # Skip if already has courses
        if row.get("courses_taught", "").strip():
            continue

        # Skip garbage
        if not name or name.startswith("#"):
            continue

        scraped += 1
        dept = row.get("department", "?")
        print(f"[{scraped}/{needs_scraping}] {name} ({dept})...", end=" ", flush=True)

        try:
            courses = scrape_one(row.get("Name", name), TERMS, session)
        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1
            continue

        if courses:
            row["courses_taught"] = format_courses(courses)
            found += 1
            print(f"=> {len(courses)} course(s)")
        else:
            not_found += 1
            print(f"=> none")

        # Save progress every 50 professors
        if scraped % 50 == 0:
            save_csv(rows, fieldnames)
            pct = (found / scraped * 100) if scraped else 0
            print(f"\n  --- Checkpoint: {scraped}/{needs_scraping} done, "
                  f"{found} found ({pct:.0f}%), saved to CSV ---\n")

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
