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
    text = re.sub(r'[^a-z0-9 ]', '', text)
    return text

def fetch_all_terplink_events(save_to_file=True, filename="terplink_events_human.json"):
    base_url = "https://terplink.umd.edu/api/discovery/event/search"
    params = {
        "orderByField": "startDate",
        "orderByDirection": "ascending",
        "take": 100,
        "status": "Approved",
        # skip is set dynamically below
    }

    all_events = []
    skip = 0
    page = 0

    while True:
        params["skip"] = skip
        page += 1
        print(f"Requesting page {page} — skip={skip}")  # logging

        response = requests.get(base_url, params=params)
        print("  HTTP status:", response.status_code)
        try:
            data = response.json()
        except Exception as e:
            print("  Failed to parse JSON:", e)
            break

        # Log the raw data keys & preview
        print("  Keys in response:", list(data.keys()))
        events_batch = data.get("value", [])
        print("  Number of events in this batch:", len(events_batch))

        if not events_batch:
            print("  No more events; breaking.")
            break

        for e in events_batch:
            start_iso = e.get("startsOn")
            end_iso = e.get("endsOn")

            def convert(iso_string):
                if not iso_string:
                    return None
                dt = datetime.datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
                return dt.strftime("%A, %B %d, %Y at %I:%M %p")

            start_human = convert(start_iso)
            end_human = convert(end_iso)

            description_text = strip_html(e.get("description"))
            description_text = clean_text(description_text)

            normalized_name = normalize_text(e.get("name"))
            normalized_description = normalize_text(description_text)

            all_events.append({
                "name": e.get("name"),
                "organization": e.get("organizationName"),
                "description": description_text,
                "location": e.get("location"),
                "start": start_human,
                "end": end_human,
                "startISO": start_iso,
                "endISO": end_iso,
                "normalized_name": normalized_name,
                "normalized_description": normalized_description
            })

        skip += params["take"]

    print("Total events fetched:", len(all_events))

    if save_to_file:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_events, f, indent=2)
        print(f"Saved {len(all_events)} events to {filename}")

    return all_events

if __name__ == "__main__":
    fetch_all_terplink_events()