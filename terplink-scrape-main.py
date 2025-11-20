import requests
import datetime
import json
import re
from html.parser import HTMLParser


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        self.text_parts.append(data)

    def get_text(self):
        return ''.join(self.text_parts)


def strip_html(html_string):
    if not html_string:
        return ""
    parser = HTMLTextExtractor()
    parser.feed(html_string)
    return parser.get_text()


def clean_text(text):
    if not text:
        return ""
    text = text.replace("\u00a0", " ")
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def normalize_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return text


def fetch_all_terplink_events(save_to_file=True, filename="terplink_events_human.json"):
    base_url = "https://terplink.umd.edu/api/discovery/event/search"

    params = {
        "orderByField": "startDate",
        "orderByDirection": "ascending",
        "take": 100,
        "status": "Approved",
    }

    today = datetime.datetime.now(datetime.UTC)
    all_events = []
    seen_ids = set()
    last_batch = None
    skip = 0
    page = 0
    hit_past_event = False

    while True:
        params["skip"] = skip
        page += 1

        print(f"Requesting page {page} — skip={skip}")

        response = requests.get(base_url, params=params)
        print("  HTTP status:", response.status_code)

        try:
            data = response.json()
        except:
            print("  JSON parse error")
            break

        events_batch = data.get("value", [])
        print("  Events in this batch:", len(events_batch))

        # Stop if empty
        if not events_batch:
            print("  No more events — end.")
            break

        # Stop if duplicate
        if last_batch is not None and events_batch == last_batch:
            print("  Duplicate page — end.")
            break

        last_batch = events_batch

        for e in events_batch:
            start_iso = e.get("startsOn")
            if not start_iso:
                continue

            start_dt = datetime.datetime.fromisoformat(start_iso.replace("Z", "+00:00"))

            # STOP pagination once we hit a past event
            if start_dt < today:
                hit_past_event = True
                break

            # Process event (only future)
            description_text = clean_text(strip_html(e.get("description")))
            normalized_name = normalize_text(e.get("name"))
            normalized_description = normalize_text(description_text)

            all_events.append({
                "name": e.get("name"),
                "organization": e.get("organizationName"),
                "description": description_text,
                "location": e.get("location"),
                "start": start_dt.strftime("%A, %B %d, %Y at %I:%M %p"),
                "end": None,
                "startISO": start_iso,
                "endISO": e.get("endsOn"),
                "normalized_name": normalized_name,
                "normalized_description": normalized_description
            })

        # If we hit the past, stop
        if hit_past_event:
            print("  Hit past events — stopping pagination.")
            break

        skip += params["take"]

    print("Total future events fetched:", len(all_events))

    if save_to_file:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_events, f, indent=2)
        print(f"Saved to {filename}")

    return all_events


if __name__ == "__main__":
    fetch_all_terplink_events()