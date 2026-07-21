"""
Extend courses_taught coverage for Math / Chemistry & Biochemistry / AOSC by
querying Testudo for terms not yet tried.

batch_testudo_update.py has already been run for Fall 2026 (202608) and Spring 2026
(202601) - that's the "Fall 2026"/"Spring 2026" keys currently in courses_taught.
Three more terms are already defined in scrape_testudo_courses.py's TERM_LABELS but
were never queried: Fall 2025 (202508), Summer 2025 (202505), Winter 2025 (202412).

Scoped to just the rows in these 3 departments that currently have NO courses_taught
data at all (44 rows) rather than re-running the full ~1123-row CSV, to stay quick
and polite to Testudo. Merges into the existing per-term JSON structure exactly like
batch_testudo_update.py does - never overwrites an existing term's data.

Some of these 44 are Emeritus/Research-title faculty who may not teach in ANY of
these terms either - not all will fill in, and that's expected, not a bug.
"""

import concurrent.futures
import csv
import json
import os
import sys
import threading
import time
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrape_testudo_courses import (
    parse_name, generate_testudo_queries, build_search_url, fetch_page,
    parse_courses, TERM_LABELS, DELAY_MIN, DELAY_MAX,
)

import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, '..')
TOOLS_CSV = os.path.join(ROOT_DIR, 'tools', 'umd_faculty.csv')
ONECLIQUE_CSV = os.path.join(ROOT_DIR, 'OneClique Database - umd_faculty (1).csv')

TARGET_DEPARTMENTS = ['Mathematics', 'Chemistry & Biochemistry', 'Atmospheric & Oceanic Science']
NEW_TERMS = ['202508', '202505', '202412']  # Fall 2025, Summer 2025, Winter 2025
WORKERS = 4

_thread_local = threading.local()


def get_session():
    if not hasattr(_thread_local, 'session'):
        _thread_local.session = requests.Session()
    return _thread_local.session


def scrape_all_terms(name, terms, session):
    """Query each term independently (unlike scrape_professor, which stops at the
    first term with results) - we want every term's courses, not just one."""
    parsed = parse_name(name)
    queries = generate_testudo_queries(parsed)
    if not queries:
        return {}

    by_term = {}
    query = queries[0]  # primary query variant only, to keep request volume sane
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
            by_term[term] = courses
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
    return by_term


def main():
    with open(ONECLIQUE_CSV, encoding='utf-8', errors='replace') as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    targets = [r for r in rows
               if r.get('department', '').strip() in TARGET_DEPARTMENTS
               and not r.get('courses_taught', '').strip()]
    print(f"{len(targets)} rows with no courses_taught across {TARGET_DEPARTMENTS}")
    print(f"Trying terms: {[TERM_LABELS[t] for t in NEW_TERMS]}\n")

    lock = threading.Lock()
    found_count = 0
    done_count = 0

    def process_row(row):
        nonlocal found_count, done_count
        name = row['Name'].strip()
        session = get_session()
        by_term = scrape_all_terms(name, NEW_TERMS, session)

        with lock:
            done_count += 1
            if by_term:
                found_count += 1
                labeled = {TERM_LABELS.get(t, t): c for t, c in by_term.items()}
                row['courses_taught'] = json.dumps(labeled)
                total_courses = sum(len(c) for c in labeled.values())
                print(f"  [{done_count}/{len(targets)}] {name} ({row['department']}) "
                      f"=> {total_courses} course(s) across {list(labeled.keys())}")
            else:
                print(f"  [{done_count}/{len(targets)}] {name} ({row['department']}) => none")

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(process_row, r) for r in targets]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    print(f"\nFound courses for {found_count}/{len(targets)}")

    for out_path in (TOOLS_CSV, ONECLIQUE_CSV):
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {out_path}")


if __name__ == '__main__':
    main()
