"""
Debug script to test faculty contact and bio lookup for a single person.
This will show us what the page actually looks like and what selectors work.
"""

from playwright.sync_api import sync_playwright
import os

def debug_contact_lookup(faculty_name="Abadi, Daniel J"):
    """Test contact lookup for a single faculty member with verbose output."""

    auth_file = "umd_auth_state.json"

    if not os.path.exists(auth_file):
        print(f"ERROR: {auth_file} not found. Run login_umd.py first!")
        return

    print("=" * 70)
    print(f"DEBUG: Looking up contact info for: {faculty_name}")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Show browser
        context = browser.new_context(storage_state=auth_file)
        page = context.new_page()

        # Parse name
        name_parts = faculty_name.split(",")
        if len(name_parts) >= 2:
            last_name = name_parts[0].strip()
            first_name = name_parts[1].strip().split()[0]
        else:
            parts = faculty_name.strip().split()
            first_name = parts[0] if len(parts) >= 2 else ""
            last_name = parts[-1] if len(parts) >= 2 else faculty_name

        print(f"\nSearching for: First='{first_name}', Last='{last_name}'")

        # Navigate to directory
        print("\n1. Navigating to UMD directory...")
        page.goto("https://identity.umd.edu/search", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Take screenshot
        page.screenshot(path="debug_step1_initial.png")
        print("   Screenshot saved: debug_step1_initial.png")

        # Fill last name
        print("\n2. Filling in last name...")
        last_name_input = page.query_selector("input[name='lastName']")
        if last_name_input:
            print(f"   Found lastName input, filling with: {last_name}")
            last_name_input.fill(last_name)
        else:
            print("   WARNING: lastName input not found!")
            print("   Available inputs:", [inp.get_attribute("name") for inp in page.query_selector_all("input")])

        # Try advanced search for first name
        print("\n3. Checking for advanced search...")
        adv_link = page.query_selector("a[href='#advancedSearch']")
        if adv_link:
            print("   Found advanced search link, clicking...")
            adv_link.click()
            page.wait_for_timeout(500)

            first_name_input = page.query_selector("input[name='firstName']")
            if first_name_input and first_name:
                print(f"   Found firstName input, filling with: {first_name}")
                first_name_input.fill(first_name)
        else:
            print("   No advanced search link found")

        # Check faculty affiliation
        print("\n4. Checking faculty affiliation checkbox...")
        faculty_checkbox = page.query_selector("input[name='affiliation'][value='faculty']")
        if faculty_checkbox:
            print("   Found faculty checkbox, checking it...")
            faculty_checkbox.check()
        else:
            print("   WARNING: Faculty checkbox not found!")

        page.screenshot(path="debug_step2_filled.png")
        print("   Screenshot saved: debug_step2_filled.png")

        # Submit
        print("\n5. Submitting search...")
        submit_btn = page.query_selector("button[type='submit'], input[type='submit']")
        if submit_btn:
            print("   Found submit button, clicking...")
            submit_btn.click()
        else:
            print("   No submit button found, pressing Enter...")
            page.keyboard.press("Enter")

        # Wait for results
        print("\n6. Waiting for results...")
        page.wait_for_timeout(3000)

        page.screenshot(path="debug_step3_results.png")
        print("   Screenshot saved: debug_step3_results.png")

        # Try to find result rows
        print("\n7. Looking for result elements...")
        selectors_to_try = [
            "table.result-table tr",
            "div.search-result",
            "tr.result-row",
            "#search-results tr",
            ".results tr",
            "table tr",
            "div.result",
            "li.result"
        ]

        for selector in selectors_to_try:
            elements = page.query_selector_all(selector)
            print(f"   Selector '{selector}': Found {len(elements)} elements")
            if len(elements) > 0 and len(elements) < 20:
                for i, el in enumerate(elements[:3]):
                    text = el.inner_text()[:100]
                    print(f"      Element {i}: {text}")

        # Get full page text
        print("\n8. Full page body text (first 500 chars):")
        body_text = page.inner_text("body")
        print(body_text[:500])

        # Save HTML
        html = page.content()
        with open("debug_page_results.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("\n   Full HTML saved to: debug_page_results.html")

        print("\n" + "=" * 70)
        print("Debug complete! Check the screenshots and HTML file.")
        print("Press Ctrl+C to close the browser window...")
        print("=" * 70)

        # Keep browser open for manual inspection
        input()

        context.close()
        browser.close()

if __name__ == "__main__":
    debug_contact_lookup()
