"""
Fallback office/phone lookup via the UMD central directory (identity.umd.edu),
for faculty whose department listing/profile pages had no office data at all.

This is intentionally the LAST resort: identity.umd.edu returns the department's
central mailing address (e.g. "4176 CAMPUS DR"), not necessarily the person's
specific room, so it's coarser than what a department page gives when available.
Only used here to fill rows that are otherwise completely blank.

Requires an authenticated session (umd_auth_state.json, produced by login_umd.py,
which needs an interactive UMD login + Duo). The session captured 2026-03-26 was
still valid as of this run (verified live) despite a stale-looking cookie expiry.

Deliberately single-threaded with a multi-second delay between lookups - the site
is slow and this is explicitly a low-volume, occasional-use fallback, not a bulk
scraper.
"""

import csv
import os
import time

from playwright.sync_api import sync_playwright

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, '..')
AUTH_FILE = os.path.join(SCRIPT_DIR, 'umd_auth_state.json')
TOOLS_CSV = os.path.join(ROOT_DIR, 'tools', 'umd_faculty.csv')
ONECLIQUE_CSV = os.path.join(ROOT_DIR, 'OneClique Database - umd_faculty (1).csv')

TARGET_DEPARTMENTS = ['Mathematics', 'Chemistry & Biochemistry', 'Atmospheric & Oceanic Science']
DELAY_SECONDS = 4.0


def lookup_one(page, name):
    """Query identity.umd.edu for one name. Returns dict with address/phone/found."""
    result = {'address': '', 'phone': '', 'found': False}
    try:
        page.goto('https://identity.umd.edu/search', wait_until='networkidle', timeout=20000)
        page.wait_for_timeout(800)

        basic_input = page.query_selector("input[name='basicSearchInput']")
        if not basic_input:
            return result
        basic_input.fill(name)

        submit_btn = page.query_selector("input[name='basicSearch']")
        if submit_btn:
            submit_btn.click()
        else:
            page.keyboard.press('Enter')

        page.wait_for_timeout(2000)

        items = page.query_selector_all('div.DisplaySearchItem')
        if not items:
            return result

        item = items[0]  # take the first/most relevant result
        result['found'] = True

        addr_el = item.query_selector('div.address')
        if addr_el:
            addr_text = addr_el.inner_text().strip()
            if addr_text and 'Not Published' not in addr_text:
                result['address'] = addr_text.replace('\n', ', ')

        phone_el = item.query_selector('div.phoneNumbers')
        if phone_el:
            phone_text = phone_el.inner_text().replace('Phone:', '').strip()
            if phone_text and 'Not Published' not in phone_text:
                result['phone'] = phone_text

    except Exception as e:
        print(f"    ERROR: {e}")

    return result


def main():
    with open(ONECLIQUE_CSV, encoding='utf-8', errors='replace') as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    targets = [r for r in rows
               if r.get('department', '').strip() in TARGET_DEPARTMENTS
               and not r.get('office', '').strip()]
    print(f"{len(targets)} rows still missing office in {TARGET_DEPARTMENTS}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=AUTH_FILE)
        page = context.new_page()

        updated_office = 0
        updated_phone = 0
        for i, r in enumerate(targets, 1):
            name = r['Name'].strip()
            print(f"[{i}/{len(targets)}] {name} ({r['department']})")
            info = lookup_one(page, name)

            if not info['found']:
                print("    no directory match")
            else:
                if info['address']:
                    r['office'] = info['address']
                    updated_office += 1
                    print(f"    office: {info['address']}")
                else:
                    print("    matched, but address not published")
                if info['phone'] and not r.get('phone', '').strip():
                    r['phone'] = info['phone']
                    updated_phone += 1
                    print(f"    phone: {info['phone']}")

            time.sleep(DELAY_SECONDS)

        browser.close()

    print(f"\nUpdated office for {updated_office}, phone for {updated_phone}")

    for out_path in (TOOLS_CSV, ONECLIQUE_CSV):
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {out_path}")


if __name__ == '__main__':
    main()
