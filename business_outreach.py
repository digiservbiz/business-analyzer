
import os
import sqlite3
import requests

def fetch_and_save_businesses(query, location):
    """
    Fetches business data from Google Maps API and saves it to the database.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY" or api_key == "invalid_key":
        print("GOOGLE_MAPS_API_KEY environment variable not set or not valid. Using mocked data.")
        return fetch_and_save_businesses_mock(query, location)

    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "location": location,
        "radius": 5000,
        "key": api_key
    }
    res = requests.get(url, params=params).json()
    businesses = []
    for result in res.get("results", []):
        businesses.append({
            "name": result["name"],
            "address": result.get("formatted_address"),
            "website": result.get("website", ""),
        })

    conn = sqlite3.connect('businesses.db')
    c = conn.cursor()
    c.execute("DELETE FROM businesses")
    for business in businesses:
        try:
            c.execute("INSERT INTO businesses (name, address, website) VALUES (?, ?, ?)",
                      (business['name'], business['address'], business['website']))
        except sqlite3.IntegrityError:
            print(f"Business '{business['name']}' already exists in the database.")
    conn.commit()
    conn.close()
    print(f"Successfully fetched and saved {len(businesses)} businesses.")
    return businesses

def fetch_and_save_businesses_mock(query, location):
    """
    Mocked version of fetching business data.
    """
    businesses = [
        {"name": "The Friendly Diner", "address": "123 Main St, Anytown, USA", "website": "http://friendlydiner.com"},
        {"name": "City Books", "address": "456 Oak Ave, Anytown, USA", "website": "http://citybooks.com"},
        {"name": "Corner Cafe", "address": "789 Pine Ln, Anytown, USA", "website": "http://cornercafe.com"}
    ]

    conn = sqlite3.connect('businesses.db')
    c = conn.cursor()
    c.execute("DELETE FROM businesses")
    for business in businesses:
        try:
            c.execute("INSERT INTO businesses (name, address, website) VALUES (?, ?, ?)",
                      (business['name'], business['address'], business['website']))
        except sqlite3.IntegrityError:
            print(f"Business '{business['name']}' already exists in the database.")
    conn.commit()
    conn.close()
    print(f"Successfully fetched and saved {len(businesses)} businesses.")
    return businesses

def generate_outreach_message(business_name, website):
  """
  Generates a personalized outreach message for a given business.
  """
  if website:
    message = f"Hello {business_name}, we've noticed your business and were impressed by your website at {website}. We'd love to connect."
  else:
    message = f"Hello {business_name}, we've noticed your business and would love to connect."
  return message
