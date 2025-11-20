import requests
from bs4 import BeautifulSoup
import json
import unicodedata
import re

def normalize_text(text: str) -> str:
    """Normalize text for search."""
    if not text:
        return ""
    # Unicode normalize (curly quotes -> straight, accents simplified)
    text = unicodedata.normalize("NFKC", text)
    # Lowercase
    text = text.lower()
    # Remove punctuation except basic characters
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()

url = "https://counseling.umd.edu/outreach-consultation/wellness-series"
r = requests.get(url)
soup = BeautifulSoup(r.text, "html.parser")

cards = soup.find_all("div", class_="card")

output = []

for card in cards:

    # ------------------------
    # 1. Title
    # ------------------------
    header = card.find("div", class_="card-header")
    title = header.get_text(strip=True) if header else None
    title_norm = normalize_text(title)

    # ------------------------
    # 2. Description (<p>)
    # ------------------------
    desc_parts = []
    for p in card.find_all("p"):
        t = p.get_text(strip=True)
        if t:
            desc_parts.append(t)
    description = " ".join(desc_parts) if desc_parts else None
    description_norm = normalize_text(description)

    # ------------------------
    # 3. Dates (<li>)
    # ------------------------
    dates = []
    for li in card.find_all("li"):
        t = li.get_text(strip=True)
        if t:
            dates.append(t)

    # ------------------------
    # 4. Zoom Link
    # ------------------------
    zoom_link = None
    for a in card.find_all("a", href=True):
        if "zoom.us" in a["href"]:
            zoom_link = a["href"]
            break

    # ------------------------
    # STORE IN JSON STRUCTURE
    # ------------------------
    output.append({
        "title": title,
        "title_normalized": title_norm,

        "description": description,
        "description_normalized": description_norm,

        "dates": dates,
        "zoom_link": zoom_link
    })

# Save to JSON
with open("wellness_events_human.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=4, ensure_ascii=False)

print("Saved wellness_events.json")