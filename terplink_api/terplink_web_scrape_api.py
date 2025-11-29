import requests
import datetime
from difflib import SequenceMatcher


base_url = "https://terplink.umd.edu/api/discovery/event/search"

search_query = input("Enter a search term: ").lower().split()

params = {
   "endsAfter": datetime.datetime.now().isoformat(),
   "orderByField": "startDate",
   "orderByDirection": "ascending",
   "take": 100,
   "status": "Approved",
}

response = requests.get(base_url, params=params)
data = response.json()

def similar(a,b):
  return SequenceMatcher(None, a,b).ratio()

THRESHOLD = 0.8

for event in data["value"]:
   searchable_text = (event["name"] + " " + event["organizationName"] + event["description"]).lower()
   words = searchable_text.split()
   if any(any(similar(term,word)>THRESHOLD for word in words) for term in search_query):
    print(event["name"], "-", event["organizationName"])