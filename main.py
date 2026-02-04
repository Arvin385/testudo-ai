import json
import asyncio
from playwright.async_api import async_playwright
from deepmerge import always_merger

GRAPHQL_PATH_FRAGMENT = "/graphql"
OUTPUT_FILE = "events_deduped.json"
MAX_LOADS = 5

def deep_merge(base, update):
    return always_merger.merge(dict(base), dict(update))

def extract_events(data):
    """Extract events from the common UMD GraphQL structure."""
    if not isinstance(data, dict):
        return []
    d = data.get("data", {})
    if isinstance(d.get("events"), list):
        return d["events"]
    if isinstance(d.get("event"), dict):
        return [d["event"]]
    if "solspace_calendar" in d and isinstance(d["solspace_calendar"].get("events"), list):
        return d["solspace_calendar"]["events"]
    return []


async def main():
    deduped = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # intercept all POST requests to /graphql and log their response JSON
        async def on_response(resp):
            try:
                if GRAPHQL_PATH_FRAGMENT in resp.url and resp.request.method == "POST":
                    data = await resp.json()
                    events = extract_events(data)
                    if not events:
                        return
                    for ev in events:
                        eid = ev.get("id") or ev.get("uid")
                        if not eid:
                            continue
                        if eid in deduped:
                            deduped[eid] = deep_merge(deduped[eid], ev)
                        else:
                            deduped[eid] = ev
                    print(f"Captured {len(events)} events from {resp.url} (total unique: {len(deduped)})")
            except Exception:
                pass

        page.on("response", on_response)

        print("Opening calendar...")
        await page.goto("https://calendar.umd.edu/search", wait_until="networkidle")
        await page.wait_for_timeout(2000)

        print("Clicking 'Load More' up to 10 times...")
        for i in range(MAX_LOADS):
            try:
                button = page.locator("button:has-text('Load More')")
                if await button.count() == 0:
                    print("No Load More button found.")
                    break
                await button.first.click()
                print(f"Clicked Load More #{i+1}")
                await page.wait_for_timeout(2500)
            except Exception as e:
                print("Load More failed:", e)
                break

        print("Final wait for responses...")
        await page.wait_for_timeout(5000)

        await browser.close()

    events_list = list(deduped.values())
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(events_list, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(events_list)} events to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
