"""
Scraper specifically for A. James Clark School of Engineering faculty directories.
All Clark School departments use the same /clark/facultydir format.
"""

from playwright.sync_api import sync_playwright
import time

def scrape_clark_directory(url, department_name):
    """
    Scrape a single Clark School faculty directory page.

    Args:
        url: Full URL to the faculty directory (e.g., https://bioe.umd.edu/clark/facultydir)
        department_name: Name of the department for logging

    Returns:
        List of faculty dictionaries with their info
    """
    faculty_list = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print(f"\n=== Scraping {department_name} ===")
        print(f"URL: {url}")

        # Navigate to the page
        page.goto(url, wait_until="networkidle")
        time.sleep(2)

        # Save HTML for inspection
        html = page.content()
        with open(f"clark_debug_{department_name.replace(' ', '_')}.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved HTML to clark_debug_{department_name.replace(' ', '_')}.html")

        # Take screenshot
        page.screenshot(path=f"clark_debug_{department_name.replace(' ', '_')}.png")
        print(f"Screenshot saved to clark_debug_{department_name.replace(' ', '_')}.png")

        # Try different selectors to find faculty cards
        selectors_to_try = [
            "div.faculty-card",
            "div.clark-faculty-card",
            "div[class*='faculty']",
            "div.directory-item",
            "div.profile-card",
            "article",
            "div.views-row",
            "div.node-person",
        ]

        print("\nTrying selectors...")
        for selector in selectors_to_try:
            elements = page.query_selector_all(selector)
            print(f"  {selector}: {len(elements)} elements")

            if len(elements) > 0:
                print(f"\n  ✓ Found {len(elements)} entries with '{selector}'")

                # Try to extract info from first element
                if elements:
                    first = elements[0]
                    print("\n  First element HTML preview:")
                    print("  " + first.inner_html()[:500])

                    # Try to find name
                    name_selectors = ["h3 a", "h4 a", "a.name", "div.name a", ".field-name-title a"]
                    for ns in name_selectors:
                        name_el = first.query_selector(ns)
                        if name_el:
                            print(f"\n  Found name with '{ns}': {name_el.inner_text()}")
                            break

                    # Try to find email
                    email_selectors = ["a[href^='mailto:']", ".email a", ".field-name-email a"]
                    for es in email_selectors:
                        email_el = first.query_selector(es)
                        if email_el:
                            print(f"  Found email with '{es}': {email_el.inner_text()}")
                            break
                break

        print("\n" + "="*50)
        print("Check the HTML and screenshot files for more details!")
        print("="*50)

        browser.close()

    return faculty_list


if __name__ == "__main__":
    # Test with BioE department
    scrape_clark_directory(
        "https://bioe.umd.edu/clark/facultydir?drfilter=1",
        "Bioengineering"
    )
