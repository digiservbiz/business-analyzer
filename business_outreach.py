
import os
import sqlite3
import requests


GOOGLE_MAPS_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
INVALID_KEYS = {"", "YOUR_API_KEY", "invalid_key"}


def fetch_and_save_businesses(query, location):
    """
    Fetches business data from the Google Maps Places API and upserts into the DB.
    Falls back to mock data when no valid API key is set.

    Returns:
        list[dict] on success
        None on network/API error (caller should surface this to the user)
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if api_key in INVALID_KEYS:
        print("GOOGLE_MAPS_API_KEY not set or invalid — using mock data.")
        return fetch_and_save_businesses_mock(query, location)

    params = {
        "query": query,
        "location": location,
        "radius": 5000,
        "key": api_key,
    }

    try:
        response = requests.get(GOOGLE_MAPS_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        print("Google Maps API request timed out.")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"Google Maps API connection error: {e}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"Google Maps API HTTP error: {e}")
        return None
    except ValueError:
        print("Google Maps API returned invalid JSON.")
        return None

    status = data.get("status")
    if status == "REQUEST_DENIED":
        print("Google Maps API: REQUEST_DENIED — check your API key.")
        return None
    if status == "OVER_QUERY_LIMIT":
        print("Google Maps API: quota exceeded.")
        return None
    if status not in ("OK", "ZERO_RESULTS"):
        print(f"Google Maps API unexpected status: {status}")
        return None

    businesses = [
        {
            "name": r["name"],
            "address": r.get("formatted_address", ""),
            "website": r.get("website", ""),
        }
        for r in data.get("results", [])
    ]

    _upsert_businesses(businesses)
    print(f"Fetched and saved {len(businesses)} businesses.")
    return businesses


def fetch_and_save_businesses_mock(query, location):
    """Returns hard-coded sample businesses for testing without a real API key."""
    businesses = [
        {"name": "The Friendly Diner", "address": "123 Main St, Anytown, USA", "website": "http://friendlydiner.com"},
        {"name": "City Books",         "address": "456 Oak Ave, Anytown, USA",  "website": "http://citybooks.com"},
        {"name": "Corner Cafe",        "address": "789 Pine Ln, Anytown, USA",  "website": "http://cornercafe.com"},
    ]
    _upsert_businesses(businesses)
    print(f"Loaded {len(businesses)} mock businesses.")
    return businesses


def _upsert_businesses(businesses):
    """Inserts or updates businesses in the DB (keyed on website)."""
    conn = sqlite3.connect('businesses.db')
    try:
        for b in businesses:
            conn.execute(
                """INSERT INTO businesses (name, address, website) VALUES (?, ?, ?)
                   ON CONFLICT(website) DO UPDATE SET
                       name=excluded.name,
                       address=excluded.address""",
                (b["name"], b.get("address", ""), b.get("website", ""))
            )
        conn.commit()
    finally:
        conn.close()


def generate_outreach_message(business_name, website):
    """Generates a personalised outreach message for a given business."""
    if website:
        return (
            f"Hello {business_name},\n\n"
            f"We came across your business and were impressed by your online presence at {website}. "
            f"We'd love to explore how we might collaborate.\n\n"
            f"Would you be open to a brief conversation?\n\nBest regards"
        )
    return (
        f"Hello {business_name},\n\n"
        f"We came across your business and would love to connect. "
        f"We believe there could be a great opportunity for us to work together.\n\n"
        f"Would you be open to a brief conversation?\n\nBest regards"
    )
