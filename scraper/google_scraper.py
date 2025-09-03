import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

def fetch_business_data(query, location):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "location": location,
        "radius": 5000,
        "key": GOOGLE_PLACES_API_KEY
    }
    res = requests.get(url, params=params).json()
    businesses = []
    for result in res.get("results", []):
        businesses.append({
            "name": result["name"],
            "address": result.get("formatted_address"),
            "website": result.get("website", ""),
        })
    return businesses
