"""
Backfill office location for the Mathematics department.

Root cause: math-faculty.html's K2/Joomla listing page has no literal text labels
("Title"/"Address"/"Phone") in its faculty entries - just a sequence of bare
<span class="catItemExtraFieldsValue"> values. The original scrape_math_faculty.py
(and every downstream consolidation step) used a label-based regex copied from the
Physics scraper, whose site *does* have literal labels. Against Math's label-less
HTML the regex silently matches nothing, so office was written as always empty.

Fix: classify each span by content (phone/email/url pattern) instead of by a label
that doesn't exist. The office is reliably the first non-phone/email/url span after
the title span, when present. Verified against the live-rendered listing page:
79 of 90 listed faculty have an office string; the other 11 (mostly Emeritus) simply
have no office span on the page at all - not a parsing failure.

Uses core-tools/math_faculty_listing_rendered.html, already fetched live via
Playwright (see backfill_math_expertise.py for how/why it was rendered rather than
fetched with requests - the site's cloaked-email JS needs a real browser).
"""

import csv
import os
import re

from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, '..')
LISTING_HTML = os.path.join(SCRIPT_DIR, 'math_faculty_listing_rendered.html')
TOOLS_CSV = os.path.join(ROOT_DIR, 'tools', 'umd_faculty.csv')
ONECLIQUE_CSV = os.path.join(ROOT_DIR, 'OneClique Database - umd_faculty (1).csv')


def looks_like_email(s):
    return '@' in s


def looks_like_phone(s):
    return bool(re.match(r'^[\d\s().-]{7,}$', s))


def looks_like_url(s):
    return bool(re.match(r'^(https?://|www\.)', s, re.I)) or '.edu/~' in s or '.com' in s


def norm_tokens(name):
    name = name.replace(',', ' ')
    return frozenset(t.strip('.').lower() for t in name.split() if t.strip('.'))


def extract_offices():
    """{full_name_token_set: office_string} for every faculty on the listing page."""
    with open(LISTING_HTML, encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    containers = soup.find_all('div', class_='catItemBody')

    result = {}
    for c in containers:
        title_el = c.find(['h2', 'h3', 'h4'], class_=lambda x: x and 'catItemTitle' in str(x))
        if not title_el:
            continue
        name = title_el.get_text(strip=True)
        extra = c.find('div', class_='catItemExtraFields')
        spans = extra.find_all('span', class_='catItemExtraFieldsValue') if extra else []
        texts = [s.get_text(strip=True) for s in spans if s.get_text(strip=True)]

        if len(texts) >= 2:
            candidate = texts[1]
            if not (looks_like_email(candidate) or looks_like_phone(candidate)
                    or looks_like_url(candidate)):
                result[norm_tokens(name)] = candidate
    return result


def main():
    offices = extract_offices()
    print(f"Extracted {len(offices)} office strings from the live listing page")

    with open(ONECLIQUE_CSV, encoding='utf-8', errors='replace') as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    updated = 0
    for r in rows:
        if r.get('department', '').strip() != 'Mathematics':
            continue
        if r.get('office', '').strip():
            continue  # don't overwrite anything already populated
        toks = norm_tokens(r['Name'])
        office = offices.get(toks)
        if office:
            r['office'] = office
            updated += 1
            print(f"  {r['Name']}: {office!r}")

    print(f"\nUpdated {updated} Math rows with office location")

    for out_path in (TOOLS_CSV, ONECLIQUE_CSV):
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {out_path}")


if __name__ == '__main__':
    main()
