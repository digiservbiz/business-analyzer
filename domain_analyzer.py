"""
Domain Analyzer — extracts industry, location, and search intent from a domain name.
"""

import re

# ---------------------------------------------------------------------------
# Location signals — city/country keywords commonly used in domains
# ---------------------------------------------------------------------------
LOCATIONS = {
    # Cities
    "dubai": "Dubai", "london": "London", "paris": "Paris",
    "newyork": "New York", "nyc": "New York", "losangeles": "Los Angeles",
    "la": "Los Angeles", "chicago": "Chicago", "houston": "Houston",
    "toronto": "Toronto", "sydney": "Sydney", "melbourne": "Melbourne",
    "singapore": "Singapore", "hongkong": "Hong Kong", "tokyo": "Tokyo",
    "berlin": "Berlin", "amsterdam": "Amsterdam", "madrid": "Madrid",
    "rome": "Rome", "milan": "Milan", "barcelona": "Barcelona",
    "miami": "Miami", "vegas": "Las Vegas", "lasvegas": "Las Vegas",
    "boston": "Boston", "seattle": "Seattle", "denver": "Denver",
    "dallas": "Dallas", "atlanta": "Atlanta", "phoenix": "Phoenix",
    "sandiego": "San Diego", "sf": "San Francisco", "sanfrancisco": "San Francisco",
    "austin": "Austin", "nashville": "Nashville", "portland": "Portland",
    "manchester": "Manchester", "birmingham": "Birmingham", "glasgow": "Glasgow",
    "edinburgh": "Edinburgh", "leeds": "Leeds", "bristol": "Bristol",
    "abudhabi": "Abu Dhabi", "riyadh": "Riyadh",
    "cairo": "Cairo", "nairobi": "Nairobi", "lagos": "Lagos",
    "mumbai": "Mumbai", "delhi": "Delhi", "bangalore": "Bangalore",
    "jakarta": "Jakarta", "kualalumpur": "Kuala Lumpur", "kl": "Kuala Lumpur",
    "bangkok": "Bangkok", "seoul": "Seoul", "beijing": "Beijing",
    "shanghai": "Shanghai", "moscow": "Moscow", "istanbul": "Istanbul",
    "johannesburg": "Johannesburg", "capetown": "Cape Town",
    # Countries
    "usa": "United States", "uk": "United Kingdom", "uae": "UAE",
    "canada": "Canada", "australia": "Australia", "india": "India",
    "germany": "Germany", "france": "France", "italy": "Italy",
    "spain": "Spain", "brazil": "Brazil", "mexico": "Mexico",
    "netherlands": "Netherlands", "sweden": "Sweden", "norway": "Norway",
    "denmark": "Denmark", "switzerland": "Switzerland", "austria": "Austria",
    "portugal": "Portugal", "greece": "Greece", "turkey": "Turkey",
    "israel": "Israel", "saudiarabia": "Saudi Arabia", "qatar": "Qatar",
    "egypt": "Egypt", "nigeria": "Nigeria", "ghana": "Ghana",
    "kenya": "Kenya", "ethiopia": "Ethiopia", "tanzania": "Tanzania",
    "pakistan": "Pakistan", "bangladesh": "Bangladesh", "srilanka": "Sri Lanka",
    "philippines": "Philippines", "vietnam": "Vietnam", "thailand": "Thailand",
    "malaysia": "Malaysia", "indonesia": "Indonesia", "newzealand": "New Zealand",
    "argentina": "Argentina", "chile": "Chile", "colombia": "Colombia",
    "peru": "Peru",
}

# ---------------------------------------------------------------------------
# Industry keyword → Google Maps search term mapping
# ---------------------------------------------------------------------------
INDUSTRIES = {
    # Food & Drink
    "restaurant": "restaurants", "restaurants": "restaurants",
    "pizza": "pizza restaurants", "burger": "burger restaurants",
    "sushi": "sushi restaurants", "cafe": "cafes", "coffee": "coffee shops",
    "bakery": "bakeries", "bar": "bars", "pub": "pubs",
    "food": "restaurants", "dining": "restaurants", "kitchen": "restaurants",
    "grill": "grill restaurants", "bbq": "BBQ restaurants",
    "takeaway": "takeaway restaurants", "delivery": "food delivery",
    "catering": "catering companies", "diner": "diners",
    # Health & Beauty
    "salon": "hair salons", "hair": "hair salons", "beauty": "beauty salons",
    "spa": "spas", "nail": "nail salons", "barber": "barbers",
    "gym": "gyms", "fitness": "fitness centers", "yoga": "yoga studios",
    "dental": "dentists", "dentist": "dentists", "medical": "medical clinics",
    "clinic": "medical clinics", "pharmacy": "pharmacies", "optician": "opticians",
    "physio": "physiotherapists", "therapy": "therapy clinics",
    "vet": "veterinarians", "veterinary": "veterinarians",
    # Professional Services
    "lawyer": "law firms", "legal": "law firms", "law": "law firms",
    "attorney": "law firms", "solicitor": "solicitors",
    "accountant": "accounting firms", "accounting": "accounting firms",
    "finance": "financial services", "insurance": "insurance companies",
    "realestate": "real estate agencies", "property": "property agencies",
    "estate": "real estate agencies", "mortgage": "mortgage brokers",
    "consultant": "consulting firms", "consulting": "consulting firms",
    # Trades & Home
    "plumber": "plumbers", "plumbing": "plumbers",
    "electrician": "electricians", "electric": "electricians",
    "builder": "builders", "construction": "construction companies",
    "roofing": "roofing companies", "roofer": "roofing companies",
    "painter": "painters", "painting": "painters",
    "cleaner": "cleaning companies", "cleaning": "cleaning companies",
    "landscaping": "landscaping companies", "gardening": "gardeners",
    "locksmith": "locksmiths", "hvac": "HVAC companies",
    "flooring": "flooring companies", "carpenter": "carpenters",
    # Retail & Commerce
    "shop": "shops", "store": "stores", "boutique": "boutiques",
    "fashion": "fashion stores", "clothing": "clothing stores",
    "furniture": "furniture stores", "jewellery": "jewellery stores",
    "jewelry": "jewelry stores", "electronics": "electronics stores",
    "pet": "pet shops", "toys": "toy stores", "sports": "sports stores",
    "books": "bookstores",
    # Tech & Digital
    "tech": "technology companies", "software": "software companies",
    "digital": "digital agencies", "web": "web design agencies",
    "it": "IT companies", "app": "app development companies",
    "marketing": "marketing agencies", "seo": "SEO agencies",
    "media": "media companies", "design": "design agencies",
    "agency": "agencies", "studio": "studios",
    # Transport & Logistics
    "taxi": "taxi companies", "cab": "taxi companies",
    "transport": "transport companies", "logistics": "logistics companies",
    "courier": "courier services",
    "moving": "moving companies", "removal": "removal companies",
    "car": "car dealers", "auto": "car dealers", "garage": "garages",
    "mechanic": "mechanics", "driving": "driving schools",
    # Education
    "school": "schools", "academy": "academies", "tutor": "tutors",
    "tutoring": "tutoring centers", "college": "colleges",
    "training": "training centers", "coaching": "coaching centers",
    "language": "language schools", "music": "music schools",
    # Hospitality
    "hotel": "hotels", "motel": "motels", "hostel": "hostels",
    "airbnb": "holiday rentals", "rental": "rental companies",
    "travel": "travel agencies", "tour": "tour operators",
    "wedding": "wedding planners", "events": "event planners",
    "photography": "photographers", "photo": "photographers",
}

# Free/weak website builders — signal low web presence
WEAK_DOMAINS = {
    "wix.com", "wixsite.com", "wordpress.com", "squarespace.com",
    "weebly.com", "jimdo.com", "godaddywebsites.com", "yolasite.com",
    "webflow.io", "notion.site", "carrd.co", "strikingly.com",
    "site123.me", "webnode.com", "mozello.com", "ucraft.net",
}


def _strip_tld(domain: str) -> str:
    """Remove TLD and return the registrable part."""
    domain = domain.lower().strip()
    # Remove common TLDs
    for tld in [".co.uk", ".org.uk", ".me.uk", ".com.au", ".co.nz",
                ".co.za", ".co.in", ".com", ".net", ".org", ".io",
                ".co", ".uk", ".us", ".ca", ".au", ".de", ".fr",
                ".es", ".it", ".nl", ".info", ".biz", ".online",
                ".shop", ".store", ".tech", ".agency", ".app"]:
        if domain.endswith(tld):
            domain = domain[: -len(tld)]
            break
    return domain


def _tokenize(name: str) -> list[str]:
    """Split a domain name into lowercase tokens."""
    # Split on hyphens and numbers
    parts = re.split(r"[-_0-9]+", name)
    # Also split CamelCase
    tokens = []
    for part in parts:
        # Insert space before uppercase letters
        split = re.sub(r"([A-Z])", r" \1", part).strip()
        tokens.extend(split.lower().split())
    return [t for t in tokens if len(t) > 1]


def analyze_domain(domain: str) -> dict:
    """
    Parse a domain name and return:
        - domain: cleaned domain string
        - name: registrable part without TLD
        - tokens: list of keywords
        - location: detected city/country or None
        - industry: detected Google Maps search term or None
        - search_query: suggested Google Maps query
    """
    name = _strip_tld(domain)
    tokens = _tokenize(name)

    # Detect location — check concatenated tokens too (e.g. "newyork")
    location = None
    location_tokens = set()
    combined = "".join(tokens)
    for key, city in LOCATIONS.items():
        if key in combined or key in tokens:
            location = city
            # Mark which tokens contributed
            for t in tokens:
                if t in key or key in t:
                    location_tokens.add(t)
            break

    # Detect industry from remaining tokens
    industry = None
    industry_token = None
    for token in tokens:
        if token in location_tokens:
            continue
        if token in INDUSTRIES:
            industry = INDUSTRIES[token]
            industry_token = token
            break

    # Build Google Maps search query
    if industry and location:
        search_query = f"{industry} in {location}"
    elif industry:
        search_query = industry
    elif location:
        search_query = f"businesses in {location}"
    else:
        search_query = " ".join(tokens)

    return {
        "domain": domain.lower().strip(),
        "name": name,
        "tokens": tokens,
        "location": location,
        "industry": industry or ", ".join(tokens),
        "search_query": search_query,
    }


def is_weak_website(url: str) -> bool:
    """Return True if the URL points to a free website builder or is empty."""
    if not url:
        return True
    url = url.lower().strip()
    return any(weak in url for weak in WEAK_DOMAINS)


def generate_pitch_email(domain: str, business_name: str, asking_price: float = 0) -> dict:
    """Generate a personalised domain pitch email for a business."""
    price_line = f" We're asking ${asking_price:,.0f}." if asking_price > 0 else ""

    subject = f"{business_name} — {domain} is available"
    body = (
        f"Hi {business_name},\n\n"
        f"I came across your business and wanted to reach out about an opportunity.\n\n"
        f"I currently own the domain {domain}, which I believe could be a strong fit "
        f"for your business — it's memorable, keyword-rich, and could help you stand "
        f"out online.{price_line}\n\n"
        f"If you're interested in learning more or making an offer, simply reply to "
        f"this email and I'll get back to you promptly.\n\n"
        f"Best regards"
    )
    return {"subject": subject, "body": body}
