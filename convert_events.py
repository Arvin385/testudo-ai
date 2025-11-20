# convert_events.py
import json
import re
import unicodedata
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser

INPUT_FILE = "calendar_events_deduped.json"
OUTPUT_FILE = "calendar_events_human.json"

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        self.text_parts.append(data)

    def get_text(self):
        return "".join(self.text_parts).strip()

def strip_html(html):
    if not html:
        return ""
    parser = HTMLTextExtractor()
    parser.feed(html)
    return parser.get_text()

# ----------------------------------------------------
# NORMALIZATION HELPERS
# ----------------------------------------------------
def normalize_text(text):
    if not text:
        return ""

    # lowercase
    text = text.lower()

    # remove accents
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # remove punctuation (keep alnum + space)
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def iso_date_from_human(date_str):
    """Convert 'Thu Sep 11' → '2025-09-11' IF year exists in original."""
    try:
        # If year missing, return empty
        if len(date_str.split()) == 3:
            return ""
        dt = datetime.strptime(date_str, "%a %b %d, %Y")
        return dt.date().isoformat()
    except:
        return ""


def human_readable_date(date_str):
    if not date_str:
        return "Not provided"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%a %b %d, %Y")
    except:
        return date_str

def human_readable_time(time_str, all_day=False):
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
        raw_start = ev.get("startDateOnly") or ev.get("startDate") or ""
        raw_end = ev.get("endDateOnly") or ev.get("endDate") or ""

        start_date = human_readable_date(raw_start)
        end_date = human_readable_date(raw_end)

        start_time = ev.get("startTimeOnly")
        end_time = ev.get("endTimeOnly")
        all_day = ev.get("allDay", False)

        time_display = human_readable_time(
            f"{start_time} - {end_time}" if start_time or end_time else None,
            all_day
        )

        description_raw = strip_html(ev.get("description", ""))

        event = {
            "id": ev.get("id"),
            "title": ev.get("title"),
            "url": ev.get("url"),
            "start_date": start_date,
            "end_date": end_date,
            "time": time_display,
            "description": description_raw,

            # -------------------------------
            # NORMALIZED FIELDS FOR SEARCH
            # -------------------------------
            "title_normalized": normalize_text(ev.get("title", "")),
            "description_normalized": normalize_text(description_raw),
            "start_date_normalized": normalize_text(raw_start),
            "end_date_normalized": normalize_text(raw_end)
        }

        human_events.append(event)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(human_events, f, indent=2, ensure_ascii=False)

    print(f"Converted {len(human_events)} events → {OUTPUT_FILE}")


if __name__ == "__main__":
    convert_events()