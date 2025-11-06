# convert_events.py
import json
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser

INPUT_FILE = "events_deduped.json"
OUTPUT_FILE = "events_human.json"

class HTMLTextExtractor(HTMLParser):
    """Helper class to strip HTML tags and get plain text."""
    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        self.text_parts.append(data)

    def get_text(self):
        return "".join(self.text_parts).strip()

def strip_html(html):
    if not html:
        return "Not provided"
    parser = HTMLTextExtractor()
    parser.feed(html)
    return parser.get_text() or "Not provided"

def human_readable_date(date_str):
    """Convert ISO datetime to human-readable format (e.g., 'Thu Sep 11, 2025')."""
    if not date_str:
        return "Not provided"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%a %b %d, %Y")
    except Exception:
        return date_str  # fallback to raw string

def human_readable_time(time_str, all_day=False):
    """Return time or 'All Day'."""
    if all_day or not time_str:
        return "All Day"
    return time_str

def convert_events():
    if not Path(INPUT_FILE).exists():
        print(f"Input file '{INPUT_FILE}' not found.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        events = json.load(f)

    human_events = []

    for ev in events:
        start_date = ev.get("startDateOnly") or ev.get("startDate") or "Not provided"
        end_date = ev.get("endDateOnly") or ev.get("endDate") or "Not provided"

        start_time = ev.get("startTimeOnly")
        end_time = ev.get("endTimeOnly")

        all_day = ev.get("allDay", False)

        time_display = human_readable_time(
            f"{start_time} - {end_time}" if start_time or end_time else None,
            all_day
        )

        human_ev = {
            "id": ev.get("id", "Not provided"),
            "title": ev.get("title", "Not provided"),
            "url": ev.get("url", "Not provided"),
            "start_date": human_readable_date(start_date),
            "end_date": human_readable_date(end_date),
            "time": time_display,
            "description": strip_html(ev.get("description"))
        }

        human_events.append(human_ev)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(human_events, f, indent=2, ensure_ascii=False)

    print(f"Converted {len(human_events)} events to human-readable JSON: {OUTPUT_FILE}")

if __name__ == "__main__":
    convert_events()