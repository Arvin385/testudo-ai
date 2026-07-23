"""
Extend courses_taught coverage to every remaining department (not just
Math/Chem/AOSC, which backfill_courses_extra_terms.py already exhausted all
5 known Testudo terms for). Tries the 3 terms not covered by the original
batch_testudo_update.py run (Fall 2025, Summer 2025, Winter 2025).

Scoped to rows with currently-blank courses_taught, excluding Math/Chem/AOSC
(already tried and largely genuine gaps - emeritus/research titles).
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
SOURCE_CSV = os.path.join(ROOT_DIR, 'OneClique Database - umd_faculty (1).csv')
RESULTS_CSV = os.path.join(SCRIPT_DIR, '_courses_backfill_results.csv')

ALREADY_EXHAUSTED_DEPARTMENTS = {'Mathematics', 'Chemistry & Biochemistry', 'Atmospheric & Oceanic Science'}
NEW_TERMS = ['202508', '202505', '202412']  # Fall 2025, Summer 2025, Winter 2025
WORKERS = 4

_thread_local = threading.local()


def get_session():
    if not hasattr(_thread_local, 'session'):
        _thread_local.session = requests.Session()
    return _thread_local.session


def scrape_all_terms(name, terms, session):
    parsed = parse_name(name)
    queries = generate_testudo_queries(parsed)
    if not queries:
        return {}

    by_term = {}
    query = queries[0]
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
    with open(SOURCE_CSV, encoding='utf-8', errors='replace') as f:
        rows = list(csv.DictReader(f))

    targets = [
        r for r in rows
        if r.get('Name', '').strip()
        and r.get('department', '').strip() not in ALREADY_EXHAUSTED_DEPARTMENTS
        and not r.get('courses_taught', '').strip()
    ]
    print(f"{len(targets)} rows with no courses_taught (excluding already-exhausted depts)", flush=True)
    print(f"Trying terms: {[TERM_LABELS[t] for t in NEW_TERMS]}\n", flush=True)

    lock = threading.Lock()
    results = []
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
                total_courses = sum(len(c) for c in labeled.values())
                print(f"  [{done_count}/{len(targets)}] {name} ({row['department']}) "
                      f"=> {total_courses} course(s) across {list(labeled.keys())}", flush=True)
                results.append({'Name': name, 'department': row['department'], 'courses_taught': json.dumps(labeled)})
            else:
                print(f"  [{done_count}/{len(targets)}] {name} ({row['department']}) => none", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(process_row, r) for r in targets]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    print(f"\nFound courses for {found_count}/{len(targets)}", flush=True)

    with open(RESULTS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Name', 'department', 'courses_taught'])
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {RESULTS_CSV}", flush=True)


if __name__ == '__main__':
    main()
