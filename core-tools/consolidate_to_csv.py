"""
Consolidate all faculty .db files into a single master CSV.

Output: tools/umd_faculty_master.csv
Columns: Name,email,phone,office,courses_taught,key_expertise,publications,department,bio,extra_info
"""

import sqlite3
import csv
import re
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(SCRIPT_DIR, '..', 'tools')
OUTPUT_CSV = os.path.join(TOOLS_DIR, 'umd_faculty_master.csv')

# Databases in priority order (richer data first)
DATABASES = [
    {
        'path': os.path.join(TOOLS_DIR, 'clark_faculty.db'),
        'table': 'clark_faculty',
        'has_office_col': True,
        'has_departments_col': True,
    },
    {
        'path': os.path.join(TOOLS_DIR, 'cmns_faculty.db'),
        'table': 'cmns_faculty',
        'has_office_col': False,
        'has_departments_col': False,
    },
    {
        'path': os.path.join(TOOLS_DIR, 'cmsc_faculty.db'),
        'table': 'cmns_faculty',
        'has_office_col': False,
        'has_departments_col': False,
    },
    {
        'path': os.path.join(TOOLS_DIR, 'amsc_faculty.db'),
        'table': 'cmns_faculty',
        'has_office_col': False,
        'has_departments_col': False,
    },
]

# Section headers in extra_info that map to CSV columns
OFFICE_HEADERS = {'OFFICE', 'CONTACT'}
TEACHING_HEADERS = {'TEACHING'}
RESEARCH_HEADERS = {'RESEARCH', 'RESEARCH AREAS', 'RESEARCH INTERESTS'}
PUBLICATIONS_HEADERS = {'PUBLICATIONS'}

CSV_COLUMNS = [
    'Name', 'email', 'phone', 'office', 'courses_taught',
    'key_expertise', 'publications', 'department', 'bio', 'extra_info',
]

# Canonical department names: map raw variants to a single standard form.
# Applied to the *primary* department (first item in comma/semicolon-separated lists).
CANONICAL_DEPARTMENTS = {
    # Engineering
    'electrical and computer engineering':       'Electrical & Computer Engineering',
    'electrical & computer engineering':         'Electrical & Computer Engineering',
    'ece and isr':                               'Electrical & Computer Engineering',
    'civil and environmental engineering':       'Civil & Environmental Engineering',
    'civil & environmental engineering':         'Civil & Environmental Engineering',
    'chemical and biomolecular engineering':      'Chemical & Biomolecular Engineering',
    'chemical & biomolecular engineering':        'Chemical & Biomolecular Engineering',
    'fischell department of bioengineering':      'Bioengineering',
    'bioengineering':                             'Bioengineering',
    'biocomputational engineering':               'Bioengineering',
    'materials science and engineering':          'Materials Science & Engineering',
    'materials science & engineering':            'Materials Science & Engineering',
    # Sciences
    'atmospheric and oceanic science':            'Atmospheric & Oceanic Science',
    'atmospheric & oceanic science':              'Atmospheric & Oceanic Science',
    'atmosphere and oceanic science':             'Atmospheric & Oceanic Science',
    'chemistry & biochemistry':                   'Chemistry & Biochemistry',
    'chemistry':                                  'Chemistry & Biochemistry',
    'chemistry and biochemistry':                 'Chemistry & Biochemistry',
    'cell biology and molecular genetics':        'Cell Biology & Molecular Genetics',
    'cell biology & molecular genetics':          'Cell Biology & Molecular Genetics',
    # Health
    'epidemiology and biostatistics':             'Epidemiology & Biostatistics',
    'epidemiology & biostatistics':               'Epidemiology & Biostatistics',
    'division of biostatistics and bioinformatics': 'Epidemiology & Biostatistics',
    # Business (Smith School)
    'robert h. smith school of business':         'Robert H. Smith School of Business',
    'decision, operations & information technologies': 'Decision, Operations & Information Technologies',
    'department of decision, operations, & information technologies': 'Decision, Operations & Information Technologies',
    'department of decisions, operations, & information technologies': 'Decision, Operations & Information Technologies',
    'do&it':                                      'Decision, Operations & Information Technologies',
    # Full-string matches for department names that themselves contain commas
    'decision, operations & information technologies': 'Decision, Operations & Information Technologies',
    'decision, operations, and information technologies': 'Decision, Operations & Information Technologies',
    'department of decision, operations, & information technologies': 'Decision, Operations & Information Technologies',
    'department of decisions, operations, & information technologies': 'Decision, Operations & Information Technologies',
    'measurement, statistics, and evaluation':     'Measurement, Statistics & Evaluation',
    'measurement, statistics & evaluation':        'Measurement, Statistics & Evaluation',
    'division of biostatistics and bioinformatics, department of epidemiology and public health, umd, school of medicine': 'Epidemiology & Biostatistics',
    # Math / Applied Math
    'mathematics & statistics':                   'Mathematics',
    # Research institutes (when listed as sole department)
    'institute for research in electronics & applied physics': 'Institute for Research in Electronics & Applied Physics',
    'institute for research in electronics and applied physics': 'Institute for Research in Electronics & Applied Physics',
    'quantum technology center':                  'Quantum Technology Center',
    'institute for physical science & technology': 'Institute for Physical Science & Technology',
    'institute for physical science and technology': 'Institute for Physical Science & Technology',
}

# Affiliations / centers to strip when they appear as the first item in
# a comma-separated department list (they are not primary departments).
STRIP_PREFIXES = [
    'a. james clark school of engineering',
]

# Map long department names in course listings to standard UMD prefixes
DEPT_NAME_TO_PREFIX = {
    'physics': 'PHYS',
    'mathematics': 'MATH',
    'chemistry': 'CHEM',
    'biology': 'BIOL',
    'astronomy': 'ASTR',
    'geology': 'GEOL',
}


def normalize_department(raw_dept):
    """Normalize a department string to a canonical name.

    Strategy:
    1. Check if the full string matches a known canonical mapping first
       (handles names that contain commas, like "Decision, Operations & IT").
    2. Split on comma or semicolon to get the first (primary) department.
    3. Strip known non-department prefixes (e.g. 'A. James Clark School of Engineering').
    4. Look up the primary department in CANONICAL_DEPARTMENTS.
    5. Return the canonical name if found, otherwise return the primary as-is.
    """
    if not raw_dept or not raw_dept.strip():
        return raw_dept

    stripped = raw_dept.strip()

    # First: try matching the full string (handles department names with commas)
    canonical = CANONICAL_DEPARTMENTS.get(stripped.lower())
    if canonical:
        return canonical

    # Split on comma or semicolon — first item is the primary department
    parts = re.split(r'[,;]', stripped)
    primary = parts[0].strip()

    # If the first part is a school-level prefix, use the second part instead
    if len(parts) > 1 and primary.lower() in STRIP_PREFIXES:
        primary = parts[1].strip()

    # Look up canonical name (case-insensitive)
    canonical = CANONICAL_DEPARTMENTS.get(primary.lower())
    if canonical:
        return canonical

    return primary


def normalize_courses(raw_text):
    """Normalize courses_taught into 'COURSEID: Name' format, one per line.

    Handles formats:
      - "- Physics 272: Introductory Physics: Fields"
      - "ENCH 250: Computer Methods..."
      - "BIOE331 - Biofluids"
      - "2016, Spring, BIOE420, Bioimaging"
      - Preamble prose, semester headers, tab indentation
    """
    if not raw_text or not raw_text.strip():
        return ''

    # Clean up whitespace and dash artifacts
    text = raw_text.replace('\xa0', ' ').replace('\t', ' ')
    # Normalize en-dash/em-dash to regular dash
    for ch in [chr(0x2013), chr(0x2014), chr(0x2010), chr(0x2012)]:
        text = text.replace(ch, '-')

    lines = text.split('\n')
    courses = []  # list of "CODE: Name" strings
    seen = set()  # track CODE to deduplicate

    for line in lines:
        line = line.strip().lstrip('-').lstrip('•').strip()
        if not line:
            continue

        extracted = _extract_course(line)
        if extracted:
            for code, name in extracted:
                if code not in seen:
                    seen.add(code)
                    courses.append(f"{code}: {name}" if name else code)

    return '\n'.join(courses)


def _extract_course(line):
    """Try to extract (CODE, Name) pairs from a single line.

    Returns list of (code, name) tuples, or empty list if no course found.
    """
    # Skip pure prose / semester headers / URLs
    if re.match(r'^(please see|professor |dr\. |courses? \d{4}|fall \d|spring \d|summer \d|winter \d|university of|current courses|previously taught|course description|courses taught|graduate courses)',
                line, re.IGNORECASE):
        return []
    if line.startswith('http'):
        return []

    # Pattern A: "YEAR, Semester, CODE, Name" (e.g. "2016, Spring, BIOE420, Bioimaging")
    m = re.match(r'^\d{4},\s*\w+,\s*([A-Z]{2,6}\d{3}[A-Z]?)\s*,\s*(.+)', line)
    if m:
        return [(m.group(1), m.group(2).strip())]

    # Pattern B: "DeptName NNN: Course Title" (e.g. "Physics 272: Intro...")
    # Also handles "Physics 272 & 272H: Title" -> two entries
    m = re.match(r'^(Physics|Mathematics|Chemistry|Biology|Astronomy|Geology)\s+(\d{3}[A-Z]?)(?:\s*&\s*(\d{3}[A-Z]?))?\s*:\s*(.+)',
                 line, re.IGNORECASE)
    if m:
        prefix = DEPT_NAME_TO_PREFIX.get(m.group(1).lower(), m.group(1).upper()[:4])
        name = m.group(4).strip()
        results = [(f"{prefix}{m.group(2)}", name)]
        if m.group(3):
            results.append((f"{prefix}{m.group(3)}", name))
        return results

    # Pattern C: Standard "CODE NNN: Name" or "CODE NNN - Name" (including en-dash/em-dash)
    # Matches ENME 610, BIOE331, ENCE 688, PHYS401, HACS 200, PLCY699B, etc.
    m = re.match(r'^([A-Z]{2,6})\s*(\d{3}[A-Z]{0,2}(?:/[A-Z]{2,6}\s*\d{3}[A-Z]{0,2})?)\s*[-:]\s*(.+)', line)
    if m:
        code = f"{m.group(1)}{m.group(2)}".replace(' ', '')
        name = m.group(3).strip().rstrip('.')
        return [(code, name)]

    # Pattern D: Just a course code with no separator but has a name after
    # e.g. "ENME462   Vibration, Controls..."
    m = re.match(r'^([A-Z]{2,6})\s*(\d{3}[A-Z]{0,2})\s{2,}(.+)', line)
    if m:
        code = f"{m.group(1)}{m.group(2)}"
        name = m.group(3).strip()
        return [(code, name)]

    # Pattern E: Bare code "BIOE689M" or "ENCE 688" with no name on this line
    m = re.match(r'^([A-Z]{2,6})\s*(\d{3}[A-Z]{0,2})\.?\s*$', line)
    if m:
        code = f"{m.group(1)}{m.group(2)}"
        return [(code, '')]

    return []


def parse_extra_info(text):
    """Parse extra_info text into structured fields.

    Returns dict with keys: office, courses_taught, research, publications, remaining
    """
    result = {
        'office': '',
        'courses_taught': '',
        'research': '',
        'publications': '',
        'remaining': '',
    }

    if not text or not text.strip():
        return result

    # Split into sections by uppercase headers (e.g. "OFFICE:\n...", "TEACHING:\n...")
    # Pattern: line starting with uppercase words followed by colon
    section_pattern = re.compile(r'^([A-Z][A-Z &/]+):\s*$', re.MULTILINE)

    splits = section_pattern.split(text)
    # splits alternates: [preamble, header1, content1, header2, content2, ...]

    remaining_parts = []

    # Handle preamble (text before first header)
    if splits[0].strip():
        remaining_parts.append(splits[0].strip())

    # Process header-content pairs
    for i in range(1, len(splits), 2):
        header = splits[i].strip()
        content = splits[i + 1].strip() if i + 1 < len(splits) else ''

        if not content:
            continue

        if header in OFFICE_HEADERS:
            result['office'] = content
        elif header in TEACHING_HEADERS:
            result['courses_taught'] = content
        elif header in RESEARCH_HEADERS:
            result['research'] = content
        elif header in PUBLICATIONS_HEADERS:
            result['publications'] = content
        else:
            remaining_parts.append(f"{header}:\n{content}")

    result['remaining'] = '\n\n'.join(remaining_parts)
    return result


def load_db(db_config):
    """Load all rows from a database, returning normalized dicts."""
    path = db_config['path']
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found, skipping")
        return []

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(f"SELECT * FROM {db_config['table']}").fetchall()
    conn.close()

    results = []
    for row in rows:
        d = dict(row)
        entry = {
            'name': d.get('name', ''),
            'email': d.get('email', ''),
            'phone': d.get('phone', ''),
            'profile_url': d.get('profile_url', ''),
            'bio': d.get('bio', '') or '',
            'extra_info_raw': d.get('extra_info', '') or '',
        }

        # Department: clark has 'departments' column, others use source_department
        if db_config['has_departments_col']:
            entry['department'] = d.get('departments', '') or d.get('source_department', '')
        else:
            entry['department'] = d.get('source_department', '')

        # Office: clark has its own column
        if db_config['has_office_col']:
            entry['office_col'] = d.get('office', '') or ''
        else:
            entry['office_col'] = ''

        results.append(entry)

    print(f"  Loaded {len(results)} rows from {os.path.basename(path)}")
    return results


def build_csv_row(entry):
    """Convert a normalized entry dict into a CSV row dict."""
    parsed = parse_extra_info(entry['extra_info_raw'])

    # Office: prefer DB column, fall back to parsed extra_info
    office = entry['office_col'] or parsed['office']

    # Courses taught: from TEACHING section, normalized
    courses_taught = normalize_courses(parsed['courses_taught'])

    # Key expertise: combine bio + research sections
    expertise_parts = []
    if entry['bio']:
        expertise_parts.append(entry['bio'])
    if parsed['research']:
        expertise_parts.append(parsed['research'])
    key_expertise = '\n\n'.join(expertise_parts)

    # Publications: from PUBLICATIONS section
    publications = parsed['publications']

    # extra_info: everything that wasn't parsed into a specific column
    extra_info = parsed['remaining']

    return {
        'Name': entry['name'],
        'email': entry['email'],
        'phone': entry['phone'],
        'office': office,
        'courses_taught': courses_taught,
        'key_expertise': key_expertise,
        'publications': publications,
        'department': normalize_department(entry['department']),
        'bio': entry['bio'],
        'extra_info': extra_info,
    }


def main():
    print("=== Consolidating .db files to master CSV ===\n")

    all_entries = []
    seen_emails = set()
    dupes_skipped = 0

    for db_config in DATABASES:
        print(f"Processing {os.path.basename(db_config['path'])}...")
        rows = load_db(db_config)

        for entry in rows:
            email = (entry['email'] or '').strip().lower()

            # Deduplicate by email (skip if already seen)
            if email and email in seen_emails:
                dupes_skipped += 1
                continue

            if email:
                seen_emails.add(email)

            all_entries.append(entry)

    print(f"\nTotal unique entries: {len(all_entries)}")
    print(f"Duplicates skipped: {dupes_skipped}")

    # Build CSV rows
    csv_rows = [build_csv_row(e) for e in all_entries]

    # Write CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"\nWrote {len(csv_rows)} rows to {OUTPUT_CSV}")

    # Summary stats
    print("\n=== Coverage Stats ===")
    for col in CSV_COLUMNS:
        filled = sum(1 for r in csv_rows if (r.get(col) or '').strip())
        pct = (filled / len(csv_rows) * 100) if csv_rows else 0
        print(f"  {col:20s}: {filled:4d}/{len(csv_rows)} ({pct:.1f}%)")

    print("\n=== Per-Department Counts ===")
    dept_counts = {}
    for r in csv_rows:
        dept = r['department'] or '(unknown)'
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
    for dept, count in sorted(dept_counts.items(), key=lambda x: -x[1]):
        print(f"  {dept}: {count}")


if __name__ == '__main__':
    main()
