"""
Assemble the final "backfilled" CSV: full master dataset, with the
identity.umd.edu and Testudo backfill results merged in, and any field that
is STILL blank after all backfill attempts explicitly marked "No Data
Found" rather than left empty - so every non-corrupted row has a value in
every column, and that value is either real data or an explicit statement
that none could be found.

Inputs:
  - OneClique Database - umd_faculty (1).csv   (1012-row master)
  - _identity_backfill_results.csv             (email/phone/office, 371 rows attempted)
  - _courses_backfill_results.csv              (courses_taught, 283 rows attempted, 22 hits)

Rules:
  - The single '#VALUE!' row has no Name and no department - there is
    nothing to look up (no identity to search for), so it is dropped rather
    than stamped "No Data Found" across the board. Noted in the summary.
  - Never overwrites a field that already had real data.
  - identity.umd.edu placeholder text ("Not Found", "Not Published") is
    treated as no-result, not as real data.
  - publications has no backfill source in this pipeline (no scraper
    reaches it) - blank publications go straight to "No Data Found".
  - key_expertise is left untouched content-wise (including the generic
    department-stub rows); only the single genuinely blank key_expertise
    cell (which belongs to the dropped #VALUE! row anyway) would ever need
    the marker.
"""

import csv
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, '..')
MASTER_CSV = os.path.join(ROOT_DIR, 'OneClique Database - umd_faculty (1).csv')
IDENTITY_RESULTS = os.path.join(SCRIPT_DIR, '_identity_backfill_results.csv')
COURSES_RESULTS = os.path.join(SCRIPT_DIR, '_courses_backfill_results.csv')
OUTPUT_CSV = os.path.join(ROOT_DIR, 'OneClique Database - umd_faculty (backfilled).csv')

NO_DATA = 'No Data Found'
BAD_TOKENS = {'', 'N/A', 'NA', 'NONE', '#VALUE!', 'NOT FOUND', 'NOT PUBLISHED'}
BACKFILL_FIELDS = ['email', 'phone', 'office', 'courses_taught', 'publications', 'key_expertise']


def blank(v):
    return (v or '').strip().upper() in BAD_TOKENS


def load_identity_results():
    by_key = {}
    with open(IDENTITY_RESULTS, encoding='utf-8', errors='replace') as f:
        for r in csv.DictReader(f):
            key = (r['Name'].strip(), r['department'].strip())
            by_key[key] = r
    return by_key


def load_courses_results():
    by_key = {}
    with open(COURSES_RESULTS, encoding='utf-8', errors='replace') as f:
        for r in csv.DictReader(f):
            key = (r['Name'].strip(), r['department'].strip())
            by_key[key] = r
    return by_key


def main():
    with open(MASTER_CSV, encoding='utf-8', errors='replace') as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    identity_results = load_identity_results()
    courses_results = load_courses_results()

    # Drop the single unidentifiable artifact row (no Name, no department).
    rows = [r for r in rows if r.get('Name', '').strip() and r.get('department', '').strip()]

    identity_applied = {'email': 0, 'phone': 0, 'office': 0}
    courses_applied = 0
    marked_no_data = {f: 0 for f in BACKFILL_FIELDS}

    for r in rows:
        key = (r['Name'].strip(), r['department'].strip())

        idr = identity_results.get(key)
        if idr:
            for field in ('email', 'phone', 'office'):
                if blank(r.get(field)) and not blank(idr.get(field)):
                    r[field] = idr[field].strip()
                    identity_applied[field] += 1

        cr = courses_results.get(key)
        if cr and blank(r.get('courses_taught')) and not blank(cr.get('courses_taught')):
            r['courses_taught'] = cr['courses_taught'].strip()
            courses_applied += 1

        for field in BACKFILL_FIELDS:
            if blank(r.get(field)):
                r[field] = NO_DATA
                marked_no_data[field] += 1

    print("Identity backfill applied:", identity_applied)
    print("Courses backfill applied:", courses_applied)
    print("Marked 'No Data Found':", marked_no_data)
    print(f"Row count: {len(rows)} (1 unidentifiable '#VALUE!' row dropped)")

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUTPUT_CSV}")


if __name__ == '__main__':
    main()
