# playwright_safe_capture.py
from playwright.sync_api import sync_playwright
import json
import time
from pathlib import Path

CALENDAR_SEARCH_URL = "https://calendar.umd.edu/search"
GRAPHQL_PATH_FRAGMENT = "/graphql"
OUTPUT_RESPONSES_FILE = "responses.json"   # all GraphQL responses
OUTPUT_EVENTS_FILE = "events_deduped.json" # deduped events with full body
MAX_CLICKS = 50
MAX_CONSECUTIVE_NO_NEW = 3
CLICK_TIMEOUT_MS = 5000

def stable_event_key(ev: dict) -> str:
    """Return a stable dedupe key for an event dict."""
    for k in ("id", "eventId", "uid", "guid"):
        val = ev.get(k)
        if val:
            return f"id:{val}"
    # fallback: title + start + time
    return f"{ev.get('title','')[:200]}|{ev.get('startDateOnly','') or ev.get('start_date','')}|{ev.get('startTimeOnly','') or ev.get('start_time','')}"

def extract_events_from_graphql_json(data: dict):
    """Try multiple plausible paths to the events array in the GraphQL response."""
    if not isinstance(data, dict):
        return []
    # Common paths
    for path in [
        lambda d: d.get("data", {}).get("solspace_calendar", {}).get("events"),
        lambda d: d.get("data", {}).get("events"),
        lambda d: d.get("events")
    ]:
        evs = path(data)
        if isinstance(evs, list):
            return evs

    # Fallback: recursively find lists of dicts
    def find_lists(obj):
        found = []
        if isinstance(obj, list):
            if all(isinstance(i, dict) for i in obj):
                found.append(obj)
            for i in obj:
                found.extend(find_lists(i))
        elif isinstance(obj, dict):
            for v in obj.values():
                found.extend(find_lists(v))
        return found

    candidates = find_lists(data)
    if candidates:
        return max(candidates, key=len)
    return []

def main():
    Path(OUTPUT_RESPONSES_FILE).unlink(missing_ok=True)
    Path(OUTPUT_EVENTS_FILE).unlink(missing_ok=True)

    all_responses = []
    deduped_events_dict = {}  # key -> full event object
    consecutive_no_new = 0
    clicks = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        def on_response(resp):
            try:
                if GRAPHQL_PATH_FRAGMENT in resp.url and resp.request.method == "POST":
                    try:
                        data = resp.json()
                    except Exception:
                        data = json.loads(resp.text())

                    # store raw response
                    all_responses.append({"url": resp.url, "data": data})

                    # extract events
                    evs = extract_events_from_graphql_json(data)
                    if evs:
                        new = 0
                        for ev in evs:
                            key = stable_event_key(ev)
                            if key not in deduped_events_dict:
                                deduped_events_dict[key] = ev
                                new += 1
                            else:
                                # merge new fields
                                for k, v in ev.items():
                                    if k not in deduped_events_dict[key] or not deduped_events_dict[key][k]:
                                        deduped_events_dict[key][k] = v
                        print(f"Captured {len(evs)} events from {resp.url}  (new unique: {new})")
                    else:
                        print(f"Captured GraphQL response from {resp.url} but no events found.")
            except Exception as e:
                print("Error in response handler:", e)

        page.on("response", on_response)

        print("Opening page...")
        page.goto(CALENDAR_SEARCH_URL, wait_until="networkidle")
        print("Page opened. Waiting for initial GraphQL responses...")
        time.sleep(2)

        # Click "Load More" until no new events or max clicks reached
        for _ in range(MAX_CLICKS):
            clicks += 1
            load_more = page.query_selector("button:has-text('Load More')") or \
                        page.query_selector("button:has-text('Load More Events')")
            if not load_more:
                print("No 'Load More' button found. Stopping.")
                break
            try:
                before = len(deduped_events_dict)
                load_more.click()
                page.wait_for_timeout(800)
                after = len(deduped_events_dict)
                new_count = after - before
                if new_count == 0:
                    consecutive_no_new += 1
                    print(f"Click {clicks}: no new events (consecutive_no_new={consecutive_no_new})")
                else:
                    consecutive_no_new = 0
                    print(f"Click {clicks}: got {new_count} new unique events (total {after})")
                if consecutive_no_new >= MAX_CONSECUTIVE_NO_NEW:
                    print("No new events after several clicks — stopping.")
                    break
            except Exception as e:
                print("Error when clicking 'Load More':", e)
                break

        page.wait_for_timeout(1200)
        browser.close()

    # write all raw responses
    with open(OUTPUT_RESPONSES_FILE, "w", encoding="utf-8") as f:
        json.dump(all_responses, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(all_responses)} GraphQL responses to {OUTPUT_RESPONSES_FILE}")

    # write deduped events with full body
    events_deduped = list(deduped_events_dict.values())
    with open(OUTPUT_EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events_deduped, f, indent=2, ensure_ascii=False)
    print(f"Total unique events captured: {len(events_deduped)}. Written to {OUTPUT_EVENTS_FILE}")


if __name__ == "__main__":
    main()