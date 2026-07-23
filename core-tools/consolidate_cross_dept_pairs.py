"""
Consolidate cross-department same-name pairs in the clean faculty CSV into a
single row per person.

After build_clean_faculty_csv.py's filtering, 5 people still appear twice
because they hold two genuinely distinct real appointments (e.g. Louiqa
Raschid is faculty in both Computer Science and Robert H. Smith School of
Business, each with its own office/phone/expertise text). For platform use
that's still visually a "duplicate person," so this script merges each pair
into one row:

  - department: both department names joined with " / "
  - email/phone/office: both values kept, joined with " / " (they're both
    real, valid contact points - not corrupted, just two offices)
  - courses_taught: JSON dicts merged (union of term keys; on key collision
    the first row's term data wins, since none collided in practice)
  - publications: both values kept if both present, joined with " / "
  - key_expertise: NOT a simple concatenation - sent to the same local
    Ollama model (gemma3:4b) merge_and_reformat.py already uses elsewhere in
    this pipeline, with both departments' raw expertise text, asking for one
    dense combined summary that reflects the full cross-department role.

Input/output: reads and overwrites
'OneClique Database - umd_faculty (clean).csv' in place (861 -> 856 rows).
"""

import csv
import json
import os
import sys
from collections import defaultdict

try:
    import ollama
except ImportError:
    print("ERROR: ollama package not installed. Run: pip install ollama")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, '..')
CLEAN_CSV = os.path.join(ROOT_DIR, 'OneClique Database - umd_faculty (clean).csv')

MODEL = 'gemma3:4b'

PROMPT_TEMPLATE = """You are reformatting faculty data for a university query-mapping system. This professor holds appointments in TWO departments. Given the raw expertise text for each appointment below, write ONE dense combined key_expertise summary covering both.

Rules:
- Maximum 250 characters
- Start with "Expertise: " or "Expertise in "
- List core research areas, methods, and domain keywords (comma-separated), drawing from both texts, without duplicating overlapping terms
- End with UMD role/mentorship context if known, covering both departments if relevant
- Optimize for search/query matching - be keyword-dense, not prose-heavy
- Do NOT include education history, awards, or publication titles

Faculty: {name}
Department A: {dept_a}
Expertise A: {ke_a}

Department B: {dept_b}
Expertise B: {ke_b}

Respond with ONLY the reformatted combined summary, nothing else."""


def blank(v):
    return not (v or '').strip()


def merge_courses(a_json, b_json):
    def parse(s):
        s = (s or '').strip()
        if not s:
            return {}
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return {}

    merged = parse(a_json)
    for term, courses in parse(b_json).items():
        merged.setdefault(term, courses)
    return json.dumps(merged) if merged else ''


def join_field(a, b):
    a, b = (a or '').strip(), (b or '').strip()
    if a and b and a != b:
        return f"{a} / {b}"
    return a or b


def consolidate_expertise(name, dept_a, ke_a, dept_b, ke_b):
    prompt = PROMPT_TEMPLATE.format(
        name=name, dept_a=dept_a, ke_a=ke_a[:1000], dept_b=dept_b, ke_b=ke_b[:1000],
    )
    try:
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
    except Exception as e:
        print(f"    WARNING: LLM call failed for {name}: {e}")
        return join_field(ke_a, ke_b)


def main():
    with open(CLEAN_CSV, encoding='utf-8', errors='replace') as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    by_name = defaultdict(list)
    for i, r in enumerate(rows):
        by_name[r['Name'].strip()].append(i)

    pairs = {n: idxs for n, idxs in by_name.items() if len(idxs) > 1}
    print(f"{len(pairs)} cross-department same-name pairs to consolidate")

    drop_indices = set()
    for name, idxs in pairs.items():
        a, b = rows[idxs[0]], rows[idxs[1]]
        print(f"  Consolidating {name}: {a['department']} + {b['department']}")

        merged_ke = consolidate_expertise(
            name, a['department'], a['key_expertise'], b['department'], b['key_expertise'],
        )

        a['department'] = join_field(a['department'], b['department'])
        a['email'] = join_field(a['email'], b['email'])
        a['phone'] = join_field(a['phone'], b['phone'])
        a['office'] = join_field(a['office'], b['office'])
        a['publications'] = join_field(a['publications'], b['publications'])
        a['courses_taught'] = merge_courses(a['courses_taught'], b['courses_taught'])
        a['key_expertise'] = merged_ke

        print(f"    -> {a['department']}")
        print(f"    -> {merged_ke}")

        drop_indices.add(idxs[1])

    output_rows = [r for i, r in enumerate(rows) if i not in drop_indices]
    print(f"\nRow count: {len(rows)} -> {len(output_rows)}")

    with open(CLEAN_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Wrote {CLEAN_CSV}")


if __name__ == '__main__':
    main()
