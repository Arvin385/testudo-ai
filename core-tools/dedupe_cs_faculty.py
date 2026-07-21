"""
Merge duplicate Computer Science faculty rows.

Root cause: 100 CS faculty each ended up with 2-3 rows in the final CSV. One row
per person traces exactly (verified: 100/100 exact key_expertise text match) to the
hand-curated tools/umd_faculty_existing.csv - the higher-quality source that
merge_and_reformat.py always preserves untouched. The other row(s) come from a
separate, newer CS department scrape (cs_directory_page.html / cs_profile_*.html)
that has real office data (IRB room numbers) the curated source lacks, but often
only a generic "UMD Computer Science faculty." stub for key_expertise, and - for
people without a published email on the CS site - a "Contact Form: /user/NNNN/contact"
URL sitting in the email column instead of an actual address. These two sources were
appended together by department-count rather than deduped by identity, since name
formatting differs enough (no email overlap in most cases) to slip past any
email-based dedup.

Fix: per duplicate-name group, the row whose key_expertise exactly matches the
curated existing.csv entry is authoritative and kept as the base row. Any field left
blank in that base row (email/phone/office/courses_taught/publications) is backfilled
from the other row(s) in the group, but ONLY if the other value is real (a
"Contact Form: ..." placeholder is never treated as an email). The curated
key_expertise text itself is never overwritten. The non-primary row(s) are then
dropped.
"""

import csv
import os
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, '..')
EXISTING_CSV = os.path.join(ROOT_DIR, 'tools', 'umd_faculty_existing.csv')
TOOLS_CSV = os.path.join(ROOT_DIR, 'tools', 'umd_faculty.csv')
ONECLIQUE_CSV = os.path.join(ROOT_DIR, 'OneClique Database - umd_faculty (1).csv')

TARGET_DEPARTMENT = 'Computer Science'
MERGE_FIELDS = ['email', 'phone', 'office', 'courses_taught', 'publications']


def is_real_email(value):
    v = (value or '').strip()
    return bool(v) and '@' in v and not v.lower().startswith('contact form')


def is_usable(field, value):
    v = (value or '').strip()
    if not v:
        return False
    if field == 'email':
        return is_real_email(v)
    return True


def load_existing_by_name():
    with open(EXISTING_CSV, encoding='utf-8', errors='replace') as f:
        rows = list(csv.DictReader(f))
    return {r['Name'].strip(): r for r in rows if r.get('Name', '').strip()}


def main():
    existing_by_name = load_existing_by_name()

    with open(ONECLIQUE_CSV, encoding='utf-8', errors='replace') as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    by_name = defaultdict(list)
    for i, r in enumerate(rows):
        if r.get('department', '').strip() == TARGET_DEPARTMENT:
            by_name[r['Name'].strip()].append(i)

    dupes = {n: idxs for n, idxs in by_name.items() if len(idxs) > 1}
    print(f"{len(dupes)} duplicate-name groups in {TARGET_DEPARTMENT}")

    drop_indices = set()
    merged = 0
    unresolved = []

    for name, idxs in dupes.items():
        curated = existing_by_name.get(name)
        if not curated:
            unresolved.append(name)
            continue

        curated_ke = curated['key_expertise'].strip()
        primary_idx = None
        for idx in idxs:
            if rows[idx]['key_expertise'].strip() == curated_ke:
                primary_idx = idx
                break

        if primary_idx is None:
            unresolved.append(name)
            continue

        primary = rows[primary_idx]
        other_idxs = [idx for idx in idxs if idx != primary_idx]

        for idx in other_idxs:
            other = rows[idx]
            for field in MERGE_FIELDS:
                if not is_usable(field, primary.get(field)) and is_usable(field, other.get(field)):
                    primary[field] = other[field].strip()
            drop_indices.add(idx)

        merged += 1

    print(f"Merged {merged} groups")
    if unresolved:
        print(f"Could not resolve {len(unresolved)} groups (left as-is): {unresolved}")

    output_rows = [r for i, r in enumerate(rows) if i not in drop_indices]
    print(f"Row count: {len(rows)} -> {len(output_rows)}")

    for out_path in (TOOLS_CSV, ONECLIQUE_CSV):
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)
        print(f"Wrote {out_path}")


if __name__ == '__main__':
    main()
