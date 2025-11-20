import requests
import datetime
from difflib import SequenceMatcher

TOOL_SPEC = {
    "name": "terplink_web_scrape_api",
    "description": "Searches TerpLink events using fuzzy matching against a query string.",
    "parameters": ["query"]
}

def similar(a,b):
  return SequenceMatcher(None, a,b).ratio()

def search_terplink_events(query): 
  base_url = "https://terplink.umd.edu/api/discovery/event/search"

  params = {
   "endsAfter": datetime.datetime.now().isoformat(),
   "orderByField": "startDate",
   "orderByDirection": "ascending",
   "take": 100,
   "status": "Approved",
  }
  
  response = requests.get(base_url, params=params)
  data = response.json()

  THRESHOLD = 0.8
  search_terms = query.lower().split()
  results = []

  for event in data["value"]:
   searchable_text = (event["name"] + " " + event["organizationName"] + event["description"]).lower()
   words = searchable_text.split()
   if any(any(similar(term,word)>THRESHOLD for word in words) for term in search_terms):
    results.append({"Name": event["name"],
                    "Organization": event["organizationName"]})
    
  return results