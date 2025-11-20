import json

# List your input JSON files here
input_files = [
    "calendar_events_human.json",  # e.g., first JSON with "title"
    "terplink_events_human.json",  # e.g., second JSON with "title" and "url"
    "wellness_events_human.json",  # e.g., TerpLink events JSON with "name"
]

output_file = "combined_events.json"

combined = []

for filename in input_files:
    with open(filename, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            # If the JSON is a dictionary (single event), wrap in a list
            if isinstance(data, dict):
                combined.append(data)
            elif isinstance(data, list):
                combined.extend(data)
            else:
                print(f"Skipping {filename}, unknown format")
        except Exception as e:
            print(f"Failed to load {filename}: {e}")

# Save combined JSON
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(combined, f, indent=2, ensure_ascii=False)

