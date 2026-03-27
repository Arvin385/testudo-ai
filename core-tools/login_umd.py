"""
Helper script to login to UMD and save authentication state.
Run this once to authenticate, then the scraper can reuse the session.
"""

from playwright.sync_api import sync_playwright
import os

def save_umd_auth():
    """
    Opens a browser window for you to login to UMD manually.
    After you login, press Enter to save the authentication state.
    """

    auth_file = "umd_auth_state.json"

    print("=" * 60)
    print("UMD Authentication Helper")
    print("=" * 60)
    print()
    print("This will open a browser window.")
    print("Please follow these steps:")
    print("1. Login with your UMD credentials")
    print("2. Navigate to https://identity.umd.edu/search")
    print("3. Verify you can see the search form")
    print()
    print("You have 60 SECONDS to complete the login.")
    print("The window will automatically close and save your session.")
    print()

    with sync_playwright() as p:
        # Launch browser in non-headless mode so user can see it
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Navigate to the identity search page
        print("Opening UMD identity search page...")
        page.goto("https://identity.umd.edu/search")

        # Wait for user to login manually (60 seconds)
        print("\nWaiting for login...")
        import time
        for i in range(12):
            time.sleep(5)
            print(f"  {60 - (i+1)*5} seconds remaining...")

        # Save the authentication state
        context.storage_state(path=auth_file)
        print(f"\n[SUCCESS] Authentication state saved to: {auth_file}")
        print("  The scraper will now use this session for lookups.")
        print()

        browser.close()

    print("=" * 60)
    print("Setup complete! You can now run the scraper.")
    print("=" * 60)

if __name__ == "__main__":
    save_umd_auth()
