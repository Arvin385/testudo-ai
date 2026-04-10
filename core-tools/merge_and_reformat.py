"""
Merge umd_faculty_existing.csv (structured, 317 populated rows) with
umd_faculty_master.csv (938 rows, raw key_expertise) into a single
umd_faculty.csv with LLM-reformatted key_expertise.

Uses gemma4:e2b via Ollama to condense raw bio/research text into
dense <=250-char query-mapping summaries.

Usage:
    cd core-tools && ../.venv/Scripts/python.exe merge_and_reformat.py
"""

import csv
import os
import sys
import time
import json

try:
    import ollama
except ImportError:
    print("ERROR: ollama package not installed. Run: pip install ollama")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(SCRIPT_DIR, '..', 'tools')

EXISTING_CSV = os.path.join(TOOLS_DIR, 'umd_faculty_existing.csv')
MASTER_CSV = os.path.join(TOOLS_DIR, 'umd_faculty_master.csv')
OUTPUT_CSV = os.path.join(TOOLS_DIR, 'umd_faculty.csv')
CHECKPOINT_FILE = os.path.join(SCRIPT_DIR, '_reformat_checkpoint.json')

OUTPUT_COLUMNS = [
    'Name', 'email', 'phone', 'office', 'courses_taught',
    'key_expertise', 'publications', 'department',
]

MODEL = 'gemma3:4b'  # gemma4:e2b returns empty on Ollama v0.20.4; gemma3:4b is proven

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


def load_existing():
    """Load existing CSV, filter out blank rows (no Name)."""
    with open(EXISTING_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            name = (r.get('Name') or '').strip()
            if name:
                rows.append(r)
    print(f"  Loaded {len(rows)} populated rows from existing CSV")
    return rows


def load_master():
    """Load master CSV."""
    with open(MASTER_CSV, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    print(f"  Loaded {len(rows)} rows from master CSV")
    return rows


def reformat_key_expertise(name, department, raw_ke, courses_taught):
    """Call Ollama to reformat raw key_expertise into a dense <=250-char summary."""
    # Truncate raw input to avoid sending huge prompts (keep first 1500 chars)
    raw_ke_truncated = raw_ke[:1500] if len(raw_ke) > 1500 else raw_ke

    prompt = PROMPT_TEMPLATE.format(
        name=name,
        department=department,
        key_expertise=raw_ke_truncated,
        courses_taught=courses_taught or 'N/A',
    )

    try:
        response = ollama.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.3, 'num_predict': 128},
        )
        result = response['message']['content'].strip()
        # Strip any surrounding quotes the model might add
        if result.startswith('"') and result.endswith('"'):
            result = result[1:-1].strip()
        # Enforce 250 char limit
        if len(result) > 250:
            result = result[:247] + '...'
        return result
    except Exception as e:
        print(f"    WARNING: LLM call failed for {name}: {e}")
        return ''


def load_checkpoint():
    """Load checkpoint of already-reformatted emails."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_checkpoint(data):
    """Save checkpoint to disk."""
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


def main():
    print("=== Merge & Reformat Faculty CSV ===\n")

    # Step 1: Load both CSVs
    print("Loading CSVs...")
    existing_rows = load_existing()
    master_rows = load_master()

    # Step 2: Build email index of existing rows
    existing_emails = set()
    for r in existing_rows:
        email = (r.get('email') or '').strip().lower()
        if email and email != 'n/a':
            existing_emails.add(email)
    print(f"  Existing rows with email: {len(existing_emails)}")

    # Step 3: Find master-only rows
    master_only = []
    overlap_count = 0
    for r in master_rows:
        email = (r.get('email') or '').strip().lower()
        if email and email in existing_emails:
            overlap_count += 1
            continue
        # Also skip if no email and name matches an existing row
        master_only.append(r)

    print(f"  Overlap (skipped from master): {overlap_count}")
    print(f"  Master-only rows to add: {len(master_only)}")

    # Count how many need LLM calls
    need_llm = sum(1 for r in master_only if (r.get('key_expertise') or '').strip())
    no_ke = len(master_only) - need_llm
    print(f"  Need LLM reformatting: {need_llm}")
    print(f"  No key_expertise (stub only): {no_ke}")

    # Step 4: Load checkpoint for resumability
    checkpoint = load_checkpoint()
    already_done = len(checkpoint)
    if already_done:
        print(f"\n  Resuming from checkpoint: {already_done} rows already reformatted")

    # Step 5: Reformat master-only rows
    print(f"\n--- Reformatting {need_llm} rows via {MODEL} ---\n")
    reformatted_rows = []
    llm_count = 0
    start_time = time.time()

    for i, r in enumerate(master_only):
        name = (r.get('Name') or '').strip()
        email = (r.get('email') or '').strip().lower()
        department = (r.get('department') or '').strip()
        raw_ke = (r.get('key_expertise') or '').strip()
        courses = (r.get('courses_taught') or '').strip()
        publications = (r.get('publications') or '').strip()

        # Build the output row
        out_row = {
            'Name': name,
            'email': r.get('email', '').strip(),
            'phone': r.get('phone', '').strip(),
            'office': r.get('office', '').strip(),
            'courses_taught': courses,
            'key_expertise': '',
            'publications': publications,
            'department': department,
        }

        if raw_ke:
            # Check checkpoint first
            cache_key = email or name
            if cache_key in checkpoint:
                out_row['key_expertise'] = checkpoint[cache_key]
            else:
                llm_count += 1
                elapsed = time.time() - start_time
                rate = llm_count / elapsed if elapsed > 0 else 0
                remaining = (need_llm - (already_done + llm_count)) / rate if rate > 0 else 0
                # Use ascii-safe name for console output (Windows cp1252 can't print all Unicode)
                safe_name = name[:40].encode('ascii', 'replace').decode('ascii')
                print(f"  [{already_done + llm_count}/{need_llm}] {safe_name:40s} "
                      f"({rate:.1f} row/s, ~{remaining:.0f}s left)", end='', flush=True)

                result = reformat_key_expertise(name, department, raw_ke, courses)
                out_row['key_expertise'] = result
                checkpoint[cache_key] = result

                print(f"  -> {len(result)} chars")

                # Save checkpoint every 50 rows
                if llm_count % 50 == 0:
                    save_checkpoint(checkpoint)
        else:
            # No raw key_expertise: use a stub
            if department:
                out_row['key_expertise'] = f"UMD {department} faculty."
            # else leave empty

        reformatted_rows.append(out_row)

    # Final checkpoint save
    save_checkpoint(checkpoint)

    elapsed_total = time.time() - start_time
    print(f"\n--- LLM reformatting complete: {llm_count} calls in {elapsed_total:.1f}s ---\n")

    # Step 6: Combine existing + reformatted master-only
    output_rows = []

    # Add existing rows (normalized to 8 columns)
    for r in existing_rows:
        out_row = {}
        for col in OUTPUT_COLUMNS:
            val = (r.get(col) or '').strip()
            if val == 'N/A':
                val = ''
            out_row[col] = val
        output_rows.append(out_row)

    # Add reformatted master-only rows
    output_rows.extend(reformatted_rows)

    # Step 7: Write output CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {len(output_rows)} rows to {OUTPUT_CSV}")

    # Step 8: Print stats
    print("\n=== Coverage Stats ===")
    for col in OUTPUT_COLUMNS:
        filled = sum(1 for r in output_rows if (r.get(col) or '').strip())
        pct = (filled / len(output_rows) * 100) if output_rows else 0
        print(f"  {col:20s}: {filled:4d}/{len(output_rows)} ({pct:.1f}%)")

    # Check for duplicate emails
    emails = [r['email'].lower().strip() for r in output_rows if r['email'].strip()]
    dupes = len(emails) - len(set(emails))
    if dupes:
        print(f"\n  WARNING: {dupes} duplicate emails found!")
    else:
        print(f"\n  No duplicate emails.")

    # Check key_expertise lengths
    over_limit = sum(1 for r in output_rows
                     if len((r.get('key_expertise') or '')) > 250)
    print(f"  key_expertise > 250 chars: {over_limit}")

    # Cleanup checkpoint file on success
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        print("  Checkpoint file cleaned up.")


if __name__ == '__main__':
    main()
