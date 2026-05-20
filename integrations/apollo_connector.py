"""
Apollo.io REST API connector.
Searches for decision-makers at a company by name and/or domain.
Requires APOLLO_API_KEY environment variable.
"""
import os
import requests

APOLLO_API_BASE = "https://api.apollo.io/api/v1"

DECISION_MAKER_TITLES = [
    "CEO", "Owner", "Founder", "Co-Founder",
    "Marketing Director", "Digital Marketing Manager",
    "Marketing Manager", "Head of Marketing",
    "General Manager", "Managing Director",
    "Head of Digital", "Director of Marketing",
]

DECISION_MAKER_SENIORITIES = ["owner", "founder", "c_suite", "vp", "director", "manager"]

_INVALID_KEYS = {"", "YOUR_APOLLO_API_KEY", "your_apollo_api_key"}


def search_decision_makers(company_name: str, domain: str = None, max_results: int = 5):
    """
    Search Apollo.io for decision-makers at a company.

    Returns (list_of_people, error_str).
    error_str is None on success or if no results.
    Each person dict: {name, title, email, linkedin_url, source}
    """
    api_key = os.getenv("APOLLO_API_KEY", "").strip()
    if api_key in _INVALID_KEYS:
        return [], "APOLLO_API_KEY not configured — add it to .env to enable Apollo search"

    payload = {
        "api_key": api_key,
        "person_titles": DECISION_MAKER_TITLES,
        "person_seniorities": DECISION_MAKER_SENIORITIES,
        "per_page": max(1, min(max_results, 25)),
        "page": 1,
    }
    if domain:
        payload["q_organization_domains_list"] = [domain]
    else:
        payload["q_keywords"] = company_name

    try:
        resp = requests.post(
            f"{APOLLO_API_BASE}/mixed_people/search",
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        people = []
        for p in data.get("people", []):
            email = p.get("email") or ""
            # Free-plan masked emails contain asterisks — discard them
            if "*" in email:
                email = ""
            people.append({
                "name": p.get("name", ""),
                "title": p.get("title", ""),
                "email": email,
                "linkedin_url": p.get("linkedin_url", ""),
                "source": "apollo",
            })
        return people, None

    except requests.exceptions.Timeout:
        return [], "Apollo API request timed out"
    except requests.exceptions.ConnectionError:
        return [], "Could not connect to Apollo API"
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        if status == 401:
            return [], "Apollo API key is invalid (401 Unauthorized)"
        if status == 422:
            return [], "Apollo API rejected the request (422) — check your API key plan"
        return [], f"Apollo API HTTP {status} error"
    except (ValueError, KeyError) as e:
        return [], f"Unexpected response from Apollo API: {e}"
