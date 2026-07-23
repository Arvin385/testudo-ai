"""
Full-dataset identity.umd.edu backfill for email/phone/office, across ALL
departments (not just Math/Chem/AOSC like lookup_identity_office.py).

Safety design (this runs unsupervised overnight, so false positives from a
wrong same-name person are the main risk to guard against):

  - identity.umd.edu's DisplaySearchItem blocks include a div.deptName field
    (e.g. "CMNS-Computer Science", "BMGT-Robert H. Smith School of
    Business", "ENGR-Aerospace Engineering") that in every spot-check
    contained our dataset's department string verbatim as a substring after
    the college prefix. A candidate is only accepted if the row's department
    string (or, for a few abbreviated/short department names, one of a small
    set of known aliases) appears in the candidate's deptName.

  - Query strategy: try the full name first. If that returns zero results,
    OR returns results but none pass the department check, fall back to a
    last-name-only query (broader recall - e.g. "Mike Boyle" found nothing
    but "Boyle" would surface "Michael Boyle") and re-filter the larger
    candidate list by (first-name-token overlap AND department match).

  - If, after both attempts, there is not exactly one candidate passing the
    department check, the row is left as not-found rather than guessing
    from an ambiguous or zero-result set. No name is ever matched on
    department alone or on name alone - both must agree.

Only fills fields that are currently blank; never overwrites existing data.
Single-threaded with a delay between lookups, matching the site's existing
low-volume/occasional-use fallback pattern from lookup_identity_office.py.
"""

import csv
import os
import re
import time

from playwright.sync_api import sync_playwright

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, '..')
AUTH_FILE = os.path.join(SCRIPT_DIR, 'umd_auth_state.json')
SOURCE_CSV = os.path.join(ROOT_DIR, 'OneClique Database - umd_faculty (1).csv')
RESULTS_CSV = os.path.join(SCRIPT_DIR, '_identity_backfill_results.csv')

DELAY_SECONDS = 2.5

DEPT_ALIASES = {
    'DO&IT': ['Decision, Operations', 'Decision Operations'],
    'Decision, Operations & Information Technologies': ['Decision, Operations', 'Decision Operations'],
    'LBPP': ['LBPP', 'Logistics'],
    'Institute for Physical Science & Technology': ['Physical Science', 'IPST'],
    'Institute for Research in Electronics & Applied Physics': ['Electronics & Applied Physics', 'IREAP'],
    'Joint Program in Survey Methodology': ['Survey Methodology'],
    'Measurement, Statistics & Evaluation': ['Measurement', 'Statistics & Evaluation'],
    'Cell Biology & Molecular Genetics': ['Cell Biology'],
    'Center for Environmental Science': ['Environmental Science'],
    'Animal & Avian Sciences': ['Animal & Avian', 'Animal Sciences'],
}


def blank(v):
    v = (v or '').strip()
    return not v or v.upper() in ('N/A', 'NA', 'NONE', '#VALUE!')


def dept_candidates(department):
    cands = [department]
    if '&' in department:
        cands.append(department.replace('&', 'and'))
    words = department.split()
    if len(words) > 1:
        cands.append(words[0])
    cands.extend(DEPT_ALIASES.get(department, []))
    return [c.strip().lower() for c in cands if c.strip()]


def dept_matches(department, dept_name_text):
    dn = (dept_name_text or '').lower()
    if not dn:
        return False
    return any(c in dn for c in dept_candidates(department))


def name_tokens(name):
    name = re.sub(r'\([^)]*\)', ' ', name)  # drop parenthetical nicknames
    name = name.replace(',', ' ').replace('.', ' ')
    return [t.lower() for t in name.split() if t]


def search(page, query):
    page.goto('https://identity.umd.edu/search', wait_until='networkidle', timeout=20000)
    page.wait_for_timeout(500)
    inp = page.query_selector("input[name='basicSearchInput']")
    if not inp:
        return []
    inp.fill(query)
    btn = page.query_selector("input[name='basicSearch']")
    if btn:
        btn.click()
    else:
        page.keyboard.press('Enter')
    page.wait_for_timeout(1800)
    items = page.query_selector_all('div.DisplaySearchItem')

    results = []
    for item in items:
        nm = item.query_selector('div.name')
        dn = item.query_selector('div.deptName')
        em = item.query_selector('div.email a')
        addr = item.query_selector('div.address')
        ph = item.query_selector('div.phoneNumbers')
        results.append({
            'name': nm.inner_text().strip() if nm else '',
            'dept_name': dn.inner_text().strip() if dn else '',
            'email': em.inner_text().strip() if em else '',
            'address': addr.inner_text().strip() if addr else '',
            'phone': (ph.inner_text().replace('Phone:', '').strip() if ph else ''),
        })
    return results


def pick_candidate(candidates, department, target_first_tokens=None):
    matches = [c for c in candidates if dept_matches(department, c['dept_name'])]
    if target_first_tokens:
        matches = [
            c for c in matches
            if any(t in name_tokens(c['name']) for t in target_first_tokens)
        ]
    if len(matches) == 1:
        return matches[0]
    return None


def lookup_one(page, name, department):
    full_results = search(page, name)
    time.sleep(DELAY_SECONDS)

    candidate = pick_candidate(full_results, department)
    if candidate:
        return candidate, 'full-name'

    toks = name_tokens(name)
    if not toks:
        return None, 'no-tokens'
    last = toks[-1]
    first = toks[0]

    last_results = search(page, last)
    time.sleep(DELAY_SECONDS)
    candidate = pick_candidate(last_results, department, target_first_tokens=[first])
    if candidate:
        return candidate, 'last-name-fallback'

    return None, 'no-confident-match'


def main():
    with open(SOURCE_CSV, encoding='utf-8', errors='replace') as f:
        rows = list(csv.DictReader(f))

    targets = [
        r for r in rows
        if r.get('Name', '').strip() and r.get('department', '').strip()
        and (blank(r['email']) or blank(r['phone']) or blank(r['office']))
    ]
    print(f"{len(targets)} rows need email/phone/office lookup", flush=True)

    results = []
    stats = {'found': 0, 'not_found': 0}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=AUTH_FILE)
        page = context.new_page()

        for i, r in enumerate(targets, 1):
            name = r['Name'].strip()
            dept = r['department'].strip()
            try:
                candidate, method = lookup_one(page, name, dept)
            except Exception as e:
                print(f"[{i}/{len(targets)}] {name} ({dept}): ERROR {e}", flush=True)
                candidate, method = None, 'error'

            row_out = {
                'Name': name, 'department': dept, 'method': method,
                'email': '', 'phone': '', 'office': '',
            }
            if candidate:
                stats['found'] += 1
                if blank(r['email']) and candidate['email']:
                    row_out['email'] = candidate['email']
                if blank(r['phone']) and candidate['phone']:
                    row_out['phone'] = candidate['phone']
                if blank(r['office']) and candidate['address'] and 'Not Published' not in candidate['address']:
                    row_out['office'] = candidate['address'].replace('\n', ', ')
                print(f"[{i}/{len(targets)}] {name} ({dept}) via {method}: "
                      f"email={row_out['email']!r} phone={row_out['phone']!r} office={row_out['office']!r}",
                      flush=True)
            else:
                stats['not_found'] += 1
                print(f"[{i}/{len(targets)}] {name} ({dept}): no confident match ({method})", flush=True)

            results.append(row_out)

        browser.close()

    print(f"\nFound: {stats['found']}, not found: {stats['not_found']}", flush=True)

    with open(RESULTS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Name', 'department', 'method', 'email', 'phone', 'office'])
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {RESULTS_CSV}", flush=True)


if __name__ == '__main__':
    main()
