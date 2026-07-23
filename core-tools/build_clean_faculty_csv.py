"""
Build a filtered "clean" faculty CSV for platform use, derived from the full
umd_faculty dataset. Does NOT modify the master CSVs - writes a new file.

Three exclusion rules, each mechanically verified rather than judgment-based:

1. Missing identity data: blank Name or blank department. Currently just the
   single '#VALUE!' spreadsheet-error artifact row.

2. No real expertise data: key_expertise is blank/N-A, OR matches the generic
   department-stub pattern injected by merge_and_reformat.py's LLM fallback
   when no real bio text was available (e.g. "UMD Physics faculty.",
   "UMD Robert H. Smith School of Business faculty."). These carry zero
   actual expertise signal - regex: ^UMD .*\\bfaculty\\.?$ (case-insensitive).
   Verified: 137 rows match, concentrated in Physics (94) where the source
   scrape never captured bio text for most faculty.

3. Duplicated rows: exact same (Name, department) pair appearing more than
   once - a genuine duplicate row for the same appointment, not a legitimate
   cross-department joint appointment (which keeps both rows, since those are
   two distinct real appointments, e.g. Andrew Childs in both Computer
   Science and Physics). Verified only one such case exists in the current
   dataset (Nuno Martins, Electrical & Computer Engineering, appearing twice
   with different emails). Keeps whichever duplicate has more non-blank
   fields; ties broken by longer key_expertise text.

4. No email: 12 rows, all Computer Science faculty whose CS-scrape row only
   had a "Contact Form: /user/NNNN/contact" placeholder (already rejected as
   unusable, not a real address) and no curated-source email to fall back on.
   Nothing to backfill from within this dataset, so they're excluded rather
   than left with a blank contact field.
"""

import csv
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, '..')
SOURCE_CSV = os.path.join(ROOT_DIR, 'OneClique Database - umd_faculty (1).csv')
OUTPUT_CSV = os.path.join(ROOT_DIR, 'OneClique Database - umd_faculty (clean).csv')

STUB_RE = re.compile(r'^UMD .*\bfaculty\.?$', re.IGNORECASE)
BLANK_TOKENS = {'', 'N/A', 'NA', 'NONE', '#VALUE!'}


def is_blank(value):
    return (value or '').strip().upper() in BLANK_TOKENS


def has_real_expertise(value):
    v = (value or '').strip()
    if is_blank(v):
        return False
    if STUB_RE.match(v):
        return False
    return True


def completeness_score(row):
    score = sum(1 for k, v in row.items() if k != 'Name' and not is_blank(v))
    return (score, len((row.get('key_expertise') or '').strip()))


def main():
    with open(SOURCE_CSV, encoding='utf-8', errors='replace') as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    total = len(rows)

    # Rule 1: missing identity data
    step1 = [r for r in rows if not is_blank(r.get('Name')) and not is_blank(r.get('department'))]
    dropped_identity = total - len(step1)

    # Rule 2: no real expertise data
    step2 = [r for r in step1 if has_real_expertise(r.get('key_expertise'))]
    dropped_expertise = len(step1) - len(step2)

    # Rule 3: exact (Name, department) duplicates -> keep most complete
    best_by_key = {}
    for r in step2:
        key = (r['Name'].strip(), r['department'].strip())
        if key not in best_by_key or completeness_score(r) > completeness_score(best_by_key[key]):
            best_by_key[key] = r
    step3 = list(best_by_key.values())
    dropped_duplicates = len(step2) - len(step3)

    # Rule 4: no email
    step4 = [r for r in step3 if not is_blank(r.get('email'))]
    dropped_email = len(step3) - len(step4)

    print(f"Source rows: {total}")
    print(f"  Dropped (missing Name/department): {dropped_identity}")
    print(f"  Dropped (no real key_expertise, blank or generic stub): {dropped_expertise}")
    print(f"  Dropped (exact Name+department duplicate rows): {dropped_duplicates}")
    print(f"  Dropped (no email): {dropped_email}")
    print(f"Clean rows: {len(step4)}")

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(step4)
    print(f"Wrote {OUTPUT_CSV}")


if __name__ == '__main__':
    main()
