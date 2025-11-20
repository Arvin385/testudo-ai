import requests
import datetime
import json
import re
from difflib import SequenceMatcher

TOOL_SPEC = {
    "name": "combined-json-output-tool",
    "description": "Searches the combined json and returns all valid parameters for the matching events using the SequenceMatcher library.",
    "parameters": ["query"]
}

def parse_iso_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return None

def parse_normalized_date(date_str):
    # e.g., "wed nov 19"
    if not date_str:
        return None
    try:
        current_year = datetime.datetime.now().year
        return datetime.datetime.strptime(f"{date_str} {current_year}", "%a %b %d %Y")
    except Exception:
        return None

def parse_dates_list(dates_list):
    # dates_list is a list of strings like "Tuesday, October 28 from 4:00–5:00 p.m."
    # Extract the date part before " from "
    if not dates_list or not isinstance(dates_list, list):
        return []
    
    parsed_dates = []
    for date_str in dates_list:
        # Extract date portion: "Tuesday, October 28"
        m = re.match(r"^[A-Za-z]+, [A-Za-z]+ \d{1,2}", date_str)
        if m:
            date_part = m.group(0)
            try:
                # Append current year to parse
                current_year = datetime.datetime.now().year
                dt = datetime.datetime.strptime(f"{date_part} {current_year}", "%A, %B %d %Y")
                parsed_dates.append(dt)
            except Exception:
                pass
    return parsed_dates

def get_event_start_dates(event):
    # Try ISO first
    dt_iso = parse_iso_date(event.get("startISO"))
    if dt_iso:
        return [dt_iso]

    # Try normalized start_date_normalized
    dt_norm = parse_normalized_date(event.get("start_date_normalized"))
    if dt_norm:
        return [dt_norm]

    # Try dates list
    dt_list = parse_dates_list(event.get("dates"))
    if dt_list:
        return dt_list

    # Fallback: try parsing 'start' field loosely (optional)
    start_str = event.get("start")
    if start_str:
        try:
            current_year = datetime.datetime.now().year
            # Remove 'at hh:mm AM/PM' to keep only date
            date_part = re.sub(r" at \d{1,2}:\d{2} (AM|PM)", "", start_str)
            dt = datetime.datetime.strptime(f"{date_part} {current_year}", "%A, %B %d, %Y")
            return [dt]
        except Exception:
            pass

    return []


def similar(a,b):
  return SequenceMatcher(None, a,b).ratio()

def load_and_deduplicate(filename):
    with open(filename, "r", encoding="utf-8") as f:
        events = json.load(f)

    seen_ids = set()
    seen_keys = set()
    deduped_events = []

    for event in events:
        event_id = event.get("id")
        if event_id:
            if event_id not in seen_ids:
                deduped_events.append(event)
                seen_ids.add(event_id)
        else:
            # fallback key: tuple of (name lowercase, startISO or start_date_normalized or empty)
            key = (
                (event.get("title_normalized") or event.get("name") or "").lower().strip(),
                event.get("startISO") or event.get("start_date_normalized") or ""
            )
            if key not in seen_keys:
                deduped_events.append(event)
                seen_keys.add(key)
    return deduped_events

def search_local_events(query, filename="combined_events.json", date_filter=None):
    events = load_and_deduplicate(filename)

    THRESHOLD = 0.8
    search_terms = query.lower().split()
    results = []

    for event in events:
        start_dates = get_event_start_dates(event)

        if date_filter and start_dates:
            if all((sd.date() if isinstance(sd, datetime.datetime) else sd) < date_filter for sd in start_dates):
                continue

        name = event.get("title_normalized") or event.get("name", "")
        desc = event.get("description_normalized") or event.get("description", "")
        org = event.get("organizationName", "")

        searchable_text = f"{name} {org} {desc}".lower()
        words = searchable_text.split()

        if any(any(similar(term, word) > THRESHOLD for word in words) for term in search_terms):
            results.append({
                "Name": name,
                "Organization": org,
                "Description": desc,
                "StartDates": [sd.isoformat() for sd in start_dates] if start_dates else []
            })

    return results

if __name__ == "__main__":
    query = "football"
    # Example date_filter: datetime.date(2025, 11, 21)
    results = search_local_events(query)
    print(json.dumps(results, indent=2))