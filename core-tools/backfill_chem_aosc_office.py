"""
Backfill office (and phone, where missing) for Chemistry & Biochemistry and
Atmospheric & Oceanic Science.

Unlike Math, these departments' listing pages genuinely don't show office location
at all (verified: none of Chemistry's 34 listing cards contain office/room text).
The data lives on each faculty member's individual profile page instead, in a
clearly labeled block:

    <div class="field--name-field-team-contact">
      <div class="field__item">Office: 2117 Biomolecular Sciences</div>
      <div class="field__item">Phone: 301-405-3165</div>
    </div>

Both departments' enriched scrapers (scrape_chemistry_enriched.py,
scrape_aosc_enriched.py) already visit these profile pages for bio/research and
have profile_url saved in cmns_faculty.db (34/34 Chemistry, 17/17 AOSC) - this is
an additional field extraction on already-known URLs, not new scraper development.

Only touches office/phone. Does not touch key_expertise (already well-populated for
both departments - 27/34 Chemistry, 14/17 AOSC have bio).
"""

import csv
import os
import re
import sqlite3
import time

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, '..')
CMNS_DB = os.path.join(ROOT_DIR, 'tools', 'cmns_faculty.db')
TOOLS_CSV = os.path.join(ROOT_DIR, 'tools', 'umd_faculty.csv')
ONECLIQUE_CSV = os.path.join(ROOT_DIR, 'OneClique Database - umd_faculty (1).csv')

DEPARTMENTS = ['Chemistry & Biochemistry', 'Atmospheric & Oceanic Science']

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
}


def norm_tokens(name):
    name = name.replace(',', ' ')
    return frozenset(t.strip('.').lower() for t in name.split() if t.strip('.'))


def extract_contact(html):
    """Return (office, phone) parsed from the profile page's contact field, or (None, None)."""
    soup = BeautifulSoup(html, 'html.parser')
    el = soup.find(string=lambda s: s and 'Office:' in s)
    office, phone = None, None
    if el:
        office = el.strip()
        office = re.sub(r'^Office:\s*', '', office).strip()
    phone_el = soup.find(string=lambda s: s and 'Phone:' in s)
    if phone_el:
        phone = re.sub(r'^Phone:\s*', '', phone_el.strip()).strip()
    return office or None, phone or None


def fetch_profiles():
    """Query cmns_faculty.db for name+profile_url pairs across both departments."""
    conn = sqlite3.connect(CMNS_DB)
    conn.row_factory = sqlite3.Row
    result = []
    for dept in DEPARTMENTS:
        rows = conn.execute(
            'SELECT name, profile_url FROM cmns_faculty WHERE source_department = ?',
            (dept,),
        ).fetchall()
        for r in rows:
            if (r['profile_url'] or '').strip():
                result.append((dept, r['name'], r['profile_url']))
    conn.close()
    return result


def main():
    profiles = fetch_profiles()
    print(f"Found {len(profiles)} profile URLs across {DEPARTMENTS}")

    session = requests.Session()
    session.headers.update(HEADERS)

    office_map = {}  # norm_tokens(name) -> (office, phone)
    errors = []

    for i, (dept, name, url) in enumerate(profiles, 1):
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code != 200:
                errors.append((name, url, f"HTTP {resp.status_code}"))
                continue
            office, phone = extract_contact(resp.text)
            if office or phone:
                office_map[norm_tokens(name)] = (office, phone)
                print(f"  [{i}/{len(profiles)}] {name}: office={office!r} phone={phone!r}")
            else:
                print(f"  [{i}/{len(profiles)}] {name}: no contact block found")
        except requests.RequestException as e:
            errors.append((name, url, str(e)))
            print(f"  [{i}/{len(profiles)}] {name}: ERROR {e}")
        time.sleep(0.5)

    print(f"\nExtracted contact info for {len(office_map)}/{len(profiles)}")
    if errors:
        print(f"Errors: {len(errors)}")
        for name, url, err in errors:
            print(f"  {name} ({url}): {err}")

    # --- Apply to CSV, office/phone only, only where currently blank ---
    with open(ONECLIQUE_CSV, encoding='utf-8', errors='replace') as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    updated_office = 0
    updated_phone = 0
    for r in rows:
        if r.get('department', '').strip() not in DEPARTMENTS:
            continue
        toks = norm_tokens(r['Name'])
        entry = office_map.get(toks)
        if not entry:
            continue
        office, phone = entry
        if office and not r.get('office', '').strip():
            r['office'] = office
            updated_office += 1
        if phone and not r.get('phone', '').strip():
            r['phone'] = phone
            updated_phone += 1

    print(f"\nCSV: updated office for {updated_office} rows, phone for {updated_phone} rows")

    for out_path in (TOOLS_CSV, ONECLIQUE_CSV):
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {out_path}")


if __name__ == '__main__':
    main()
