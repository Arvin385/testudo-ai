"""
Backfill key_expertise for the Mathematics department.

Root cause (see SCRAPING_METHODOLOGY.md / DATA_CLEANING.md): scrape_math_faculty.py
never visited individual profile pages, so cmns_faculty.db has 88 Math rows with
empty bio/extra_info. merge_and_reformat.py's Ollama step then fell through to the
generic stub "UMD Mathematics faculty." for ~97% of Math rows.

This script does NOT re-scrape empty math.umd.edu profile pages (they contain no
bio/research content at all - verified live). Instead it pulls REAL, already-sourced
text from three places, all traceable to a live UMD page:

  1. tools/amsc_faculty.db - AMSC (Applied Math & Statistics) is cross-listed with
     Mathematics faculty and its scraper *did* capture bios. 31 Math faculty have
     real bio text sitting here already, silently dropped by consolidate_to_csv.py's
     email-based dedup (see MANUAL_EMAIL_FIXES below for why).
  2. https://www-math.umd.edu/research/faculty-research-interests.html - a page the
     department itself maintains, listing faculty name + research-area keywords
     under 10 subject headings. Matched 45 additional faculty (by last name + first
     initial, to avoid the 3-way "Yang" surname collision).
  3. MANUAL_VERIFIED_BIOS - 9 faculty whose personal websites were individually
     fetched and read by hand (not scraped programmatically) to confirm the site
     actually belongs to that person (matching name + UMD Math affiliation + email)
     before extracting their stated research interests. Source URL is recorded for
     each. 5 more faculty (Bader, Berestycki, Dancis, Kirwan, Senger) have no listed
     personal website on the department directory and were deliberately left alone
     rather than guessed at.

No LLM is used to invent content here - only to compress real sourced text into the
existing "Expertise: ..." dense format (same Ollama/gemma3:4b step every other
department's data already goes through, in merge_and_reformat.py).
"""

import csv
import os
import re
import sqlite3
import sys

from bs4 import BeautifulSoup, NavigableString, Tag

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(SCRIPT_DIR, '..', 'tools')
CMNS_DB = os.path.join(TOOLS_DIR, 'cmns_faculty.db')
AMSC_DB = os.path.join(TOOLS_DIR, 'amsc_faculty.db')
RESEARCH_HTML = os.path.join(SCRIPT_DIR, 'math_research_interests.html')

# --- 3 data-corruption fixes, verified against the LIVE rendered directory page
# (Playwright render of https://www-math.umd.edu/people/faculty.html, so the site's
# own anti-spam JS decodes the email, same as the original scrapers did) ---
# Each of these caused a duplicate row in the final CSV because the two source DBs
# had different email spellings for the same person, so consolidate_to_csv.py's
# email-based dedup didn't recognize them as the same faculty member.
MANUAL_EMAIL_FIXES = {
    frozenset(['stuart', 's', 'antman']): 'ssa@umd.edu',
    frozenset(['john', 'j', 'benedetto']): 'jjb@umd.edu',       # mailto href says jjb@math.umd.edu but is stale; live-rendered visible text says jjb@umd.edu
    frozenset(['grace', 'l', 'yang']): 'gyang1@umd.edu',        # gly@math.umd.edu appears to be a legacy/incorrect address; live page confirms gyang1@umd.edu
}

# --- Manually verified via WebFetch, one site at a time, confirming name + UMD
# Math affiliation + (where available) matching email before trusting the content ---
MANUAL_VERIFIED_BIOS = {
    frozenset(['shiferaw', 'berhanu']):
        ("Research interests: Microlocal Analysis, Several Complex Variables, and "
         "Partial Differential Equations.",
         "https://sberhanu.math.umd.edu/"),
    frozenset(['mike', 'boyle']):
        ("Research area: dynamics, specifically symbolic dynamics; affiliated with "
         "the Dynamics at Maryland research group.",
         "https://www.math.umd.edu/~mboyle/"),
    frozenset(['michael', 'brin']):
        ("Research interests: Dynamical systems and Riemannian geometry, including "
         "orbihedra, polyhedra rigidity, Hamiltonian systems, and partially "
         "hyperbolic diffeomorphisms.",
         "http://www.math.umd.edu/~mib/"),
    frozenset(['qendrim', 'gashi']):
        ("Research interests: Representation Theory, Algebraic Geometry, Number "
         "Theory and combinatorial aspects thereof.",
         "https://qendrimgashi.com/"),
    frozenset(['raymond', 'l', 'johnson']):
        ("Research area: Harmonic Analysis.",
         "https://mathweb.rice.edu/faculty/raymond-johnson"),
    frozenset(['david', 'w', 'kueker']):
        ("Research area: mathematical logic, specifically model theory; recent work "
         "on abstract elementary classes.",
         "http://www.math.umd.edu/~dwk"),
    frozenset(['ronald', 'l', 'lipsman']):
        ("Research background: representation theory of Lie groups (not actively "
         "researched in recent years); current focus on math education initiatives "
         "including differential equations, multivariable calculus, and mathematical "
         "software.",
         "http://www.math.umd.edu/~rlipsman"),
    frozenset(['peter', 'wolfe']):
        ("Research interests: Differential Equations, Numerical Analysis and "
         "Nonlinear Mechanics.",
         "http://www.math.umd.edu/~pnw"),
    frozenset(['grace', 'l', 'yang']):
        ("Research interests: Asymptotic theory in Statistics, Survival analysis, "
         "Stochastic models in physical science including radiation physics and "
         "neutron lifetime.",
         "https://math.umd.edu/~gyang1/"),
}

# Faculty individually checked for a personal website and found to have none listed
# on the department directory. Deliberately left as the generic stub rather than
# guessing at a same-named page found via open web search.
NO_VERIFIABLE_SOURCE = {
    frozenset(['uri', 'bader']),
    frozenset(['henri', 'berestycki']),
    frozenset(['jerome', 'dancis']),
    frozenset(['william', 'e', 'kirwan']),
    frozenset(['andrew', 'senger']),
}


def norm_tokens(name):
    name = name.replace(',', ' ')
    return frozenset(t.strip('.').lower() for t in name.split() if t.strip('.'))


def last_and_initial(name):
    """('balan', 'r') style key from either 'Last, First M.' or 'First M. Last'."""
    if ',' in name:
        last = name.split(',')[0].strip().split()[-1]
        rest = name.split(',', 1)[1].strip()
        first = rest.split()[0] if rest.split() else ''
    else:
        parts = name.strip().split()
        last = parts[-1]
        first = parts[0] if parts else ''
    return (last.rstrip('.,').lower(), first[:1].lower())


def load_amsc_bios():
    """All AMSC rows with non-empty bio, keyed by full-name token set.

    Not filtered by source_department: some faculty on our Math roster hold joint
    AMSC appointments tagged under a different primary department in amsc_faculty.db
    (e.g. Brian R. Hunt -> "Institute for Physical Science & Technology", Kayo Ide ->
    "Atmospheric & Oceanic Science"), even though they are Mathematics faculty in our
    CSV. The caller only looks up names that are already confirmed Math faculty in
    the CSV, and email is cross-checked as an extra safety check, so this is safe.
    """
    conn = sqlite3.connect(AMSC_DB)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute('SELECT * FROM cmns_faculty').fetchall()]
    conn.close()

    result = {}
    for r in rows:
        bio = (r['bio'] or '').strip()
        if not bio:
            continue
        result[norm_tokens(r['name'])] = (bio, (r['email'] or '').strip().lower())
    return result


def parse_research_interests_page():
    """Parse faculty-research-interests.html into {(last, initial): [(area, desc)]}."""
    with open(RESEARCH_HTML, encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.find('div', itemprop='articleBody')

    result = {}
    current_area = None
    for el in body.children:
        if getattr(el, 'name', None) == 'h3':
            current_area = el.get_text(strip=True)
        elif getattr(el, 'name', None) == 'p':
            chunks, cur = [], []
            for c in el.children:
                if getattr(c, 'name', None) == 'br':
                    chunks.append(cur)
                    cur = []
                else:
                    cur.append(c)
            if cur:
                chunks.append(cur)

            for chunk in chunks:
                name, desc_parts = None, []
                for c in chunk:
                    a_tag = None
                    if isinstance(c, Tag):
                        a_tag = c if c.name == 'a' else c.find('a')
                    if a_tag is not None and name is None:
                        name = a_tag.get_text(strip=True)
                    elif isinstance(c, Tag):
                        txt = c.get_text(' ', strip=True)
                        if txt and txt != name:
                            desc_parts.append(txt)
                    elif isinstance(c, NavigableString):
                        desc_parts.append(str(c))
                desc = ' '.join(d.strip() for d in desc_parts if d.strip()).strip(' ,')
                # Strip stray anti-spam JS text that leaks into some entries
                desc = re.sub(r'This email address.*?true\);\s*', '', desc).strip(' ,')
                if name and desc:
                    key = last_and_initial(name)
                    result.setdefault(key, []).append((current_area, desc))
    return result


def build_raw_bio(name, email, amsc_bios, research_map):
    """Return combined raw bio text for one faculty member, or '' if no real source."""
    toks = norm_tokens(name)
    parts = []

    amsc_entry = amsc_bios.get(toks)
    if amsc_entry:
        amsc_bio, amsc_email = amsc_entry
        # Cross-check email when both are known and non-trivial, as a safety net
        # against a name-token collision pulling in the wrong person's bio.
        if not email or not amsc_email or email.strip().lower() == amsc_email:
            parts.append(amsc_bio)
        else:
            print(f"  WARNING: AMSC bio found for {name!r} but email mismatch "
                  f"({email!r} vs {amsc_email!r}) - skipping AMSC bio for safety")

    key = last_and_initial(name)
    research_entries = research_map.get(key, [])
    if research_entries:
        areas_text = '; '.join(f"{area}: {desc}" for area, desc in research_entries)
        parts.append(areas_text)

    manual = MANUAL_VERIFIED_BIOS.get(toks)
    if manual:
        parts.append(manual[0])

    return '\n\n'.join(parts)


def main():
    amsc_bios = load_amsc_bios()
    research_map = parse_research_interests_page()

    conn = sqlite3.connect(CMNS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = [dict(r) for r in cur.execute(
        "SELECT * FROM cmns_faculty WHERE source_department = 'Mathematics'"
    ).fetchall()]
    print(f"Loaded {len(rows)} Mathematics rows from cmns_faculty.db")

    # Load the target CSV to get the canonical 'First [Middle] Last' names + emails,
    # since cmns_faculty.db stores 'Last, First' and (for 3 rows) has bad data.
    csv_path = os.path.join(SCRIPT_DIR, '..', 'OneClique Database - umd_faculty (1).csv')
    with open(csv_path, encoding='utf-8', errors='replace') as f:
        csv_rows = list(csv.DictReader(f))
    math_csv_rows = [r for r in csv_rows if r.get('department', '').strip() == 'Mathematics']

    seen_people = set()
    updated = 0
    no_source = 0
    for r in math_csv_rows:
        name = r['Name'].strip()
        toks = norm_tokens(name)
        email = (r.get('email') or '').strip().lower()
        if not name or name == 'Antman':
            continue  # malformed duplicate row, handled via Stuart S. Antman
        dedup_key = last_and_initial(name)
        if dedup_key in seen_people:
            continue  # duplicate (e.g. second 'Grace Yang' / 'John J. Benedetto' row)
        seen_people.add(dedup_key)

        # Apply verified email correction BEFORE the cross-check in build_raw_bio,
        # since the CSV's own email is exactly what's wrong for these 3 people.
        correct_email = MANUAL_EMAIL_FIXES.get(toks, email)

        raw_bio = build_raw_bio(name, correct_email, amsc_bios, research_map)
        if not raw_bio:
            if toks not in NO_VERIFIABLE_SOURCE:
                print(f"  WARNING: no source and not in NO_VERIFIABLE_SOURCE list: {name}")
            no_source += 1
            continue

        # Find the matching cmns_faculty.db row by name tokens (Last, First format)
        db_row = None
        for row in rows:
            if norm_tokens(row['name']) == toks:
                db_row = row
                break
        if db_row is None:
            print(f"  WARNING: no cmns_faculty.db row found for {name}, skipping DB update")
            continue

        cur.execute(
            "UPDATE cmns_faculty SET bio = ?, email = ? WHERE id = ?",
            (raw_bio, correct_email, db_row['id']),
        )
        updated += 1

    conn.commit()
    conn.close()

    print(f"\nUpdated {updated} rows with real bio text")
    print(f"No verifiable source found (left as-is): {no_source}")


if __name__ == '__main__':
    main()
