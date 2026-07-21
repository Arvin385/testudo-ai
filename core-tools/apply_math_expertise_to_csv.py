"""
Apply the backfilled Mathematics key_expertise to the actual CSVs.

Scoped, targeted update - NOT a full re-run of merge_and_reformat.py. This:
  - only touches rows where department == 'Mathematics'
  - only rewrites key_expertise for rows that were a generic stub ("UMD Mathematics
    faculty.") or one of the 3 known duplicate/corrupted identities
  - drops exactly the 3 confirmed duplicate rows (verified against the live
    department directory + cross-checked emails), keeping the correct row for each
  - does NOT add any new faculty rows (e.g. Haizhao Yang, who has real data sitting
    in our DBs but is not currently on the roster - flagged separately, not added
    here without sign-off)
  - leaves every other department and every already-populated Math row untouched

Uses the same Ollama/gemma3:4b reformatting prompt as merge_and_reformat.py, so the
output style matches every other department. The LLM only compresses/reformats real
sourced text (from backfill_math_expertise.py) into the dense format - it does not
invent content.
"""

import csv
import os
import sys

import ollama

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, '..')
MASTER_CSV = os.path.join(ROOT_DIR, 'tools', 'umd_faculty_master.csv')
TOOLS_CSV = os.path.join(ROOT_DIR, 'tools', 'umd_faculty.csv')
ONECLIQUE_CSV = os.path.join(ROOT_DIR, 'OneClique Database - umd_faculty (1).csv')

MODEL = 'gemma3:4b'

PROMPT_TEMPLATE = """You are reformatting faculty data for a university query-mapping system. Given the raw information below for a UMD professor, write a dense key_expertise summary.

Rules:
- Maximum 250 characters
- Start with "Expertise: " or "Expertise in "
- List core research areas, methods, and domain keywords (comma-separated)
- End with UMD role and mentorship/involvement context if known
- Optimize for search/query matching — be keyword-dense, not prose-heavy
- Do NOT include education history, awards, or publication titles

Faculty: {name}
Department: {department}
Raw bio/expertise text:
{key_expertise}

Courses taught: {courses_taught}

Respond with ONLY the reformatted summary, nothing else."""

# Rows to drop entirely from the CSV: confirmed duplicates of a canonical row that
# is kept and updated instead. Matched by (Name, email) exact pair to avoid
# touching anything else.
ROWS_TO_DROP = {
    ('Antman', 'ssa@umd.eduWebpage:'),
    ('Grace Yang', 'gyang1@umd.edu'),
    ('John J. Benedetto', 'jjb@math.umd.edu'),
}

# Canonical-row email corrections (verified against the live-rendered directory page)
EMAIL_FIXES = {
    'Stuart S. Antman': 'ssa@umd.edu',
    'Grace L. Yang': 'gyang1@umd.edu',
}


def norm_tokens(name):
    name = name.replace(',', ' ')
    return frozenset(t.strip('.').lower() for t in name.split() if t.strip('.'))


def last_and_initial(name):
    if ',' in name:
        last = name.split(',')[0].strip().split()[-1]
        rest = name.split(',', 1)[1].strip()
        first = rest.split()[0] if rest.split() else ''
    else:
        parts = name.strip().split()
        last = parts[-1]
        first = parts[0] if parts else ''
    return (last.rstrip('.,').lower(), first[:1].lower())


def is_stub(key_expertise):
    ke = (key_expertise or '').strip()
    return ke.lower().startswith('umd') and 'expertise' not in ke.lower()


def reformat_key_expertise(name, department, raw_ke, courses_taught):
    raw_ke_truncated = raw_ke[:1500] if len(raw_ke) > 1500 else raw_ke
    prompt = PROMPT_TEMPLATE.format(
        name=name, department=department,
        key_expertise=raw_ke_truncated, courses_taught=courses_taught or 'N/A',
    )
    response = ollama.chat(
        model=MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        options={'temperature': 0.3, 'num_predict': 128},
    )
    result = response['message']['content'].strip()
    if result.startswith('"') and result.endswith('"'):
        result = result[1:-1].strip()
    if len(result) > 250:
        result = result[:247] + '...'
    return result


def load_master_math_raw():
    """{last_and_initial_key: raw_key_expertise} for Mathematics rows in the master CSV,
    restricted to names on our current roster (matched by the caller)."""
    with open(MASTER_CSV, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    result = {}
    for r in rows:
        if r.get('department', '').strip() != 'Mathematics':
            continue
        ke = (r.get('key_expertise') or '').strip()
        if not ke:
            continue
        key = last_and_initial(r['Name'])
        result[key] = (ke, r.get('courses_taught', ''))
    return result


def main():
    master_raw = load_master_math_raw()
    print(f"Loaded raw key_expertise for {len(master_raw)} Math identities from master CSV")

    with open(ONECLIQUE_CSV, encoding='utf-8', errors='replace') as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    output_rows = []
    dropped = 0
    reformatted = 0
    skipped_no_change = 0

    for r in rows:
        dept = (r.get('department') or '').strip()
        name = (r.get('Name') or '').strip()
        email = (r.get('email') or '').strip()

        if dept == 'Mathematics' and (name, email) in ROWS_TO_DROP:
            print(f"  Dropping duplicate row: {name!r} / {email!r}")
            dropped += 1
            continue

        if dept == 'Mathematics':
            if name in EMAIL_FIXES:
                r['email'] = EMAIL_FIXES[name]

            needs_update = is_stub(r.get('key_expertise')) or name in EMAIL_FIXES
            if needs_update:
                key = last_and_initial(name)
                raw = master_raw.get(key)
                if raw:
                    raw_ke, courses = raw
                    print(f"  Reformatting: {name}")
                    new_ke = reformat_key_expertise(name, dept, raw_ke, courses)
                    r['key_expertise'] = new_ke
                    reformatted += 1
                else:
                    skipped_no_change += 1

        output_rows.append(r)

    print(f"\nDropped {dropped} duplicate rows")
    print(f"Reformatted {reformatted} rows via {MODEL}")
    print(f"Left as stub (no verified source): {skipped_no_change}")
    print(f"Final row count: {len(output_rows)} (was {len(rows)})")

    for out_path in (TOOLS_CSV, ONECLIQUE_CSV):
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)
        print(f"Wrote {out_path}")


if __name__ == '__main__':
    main()
