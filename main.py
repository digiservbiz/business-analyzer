from scraper.google_scraper import fetch_business_data
from analyzer.website_analyzer import analyze_website
from reports.report_generator import generate_report
from outreach.email_sender import send_email

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
DEFAULT_QUERY = os.getenv("DEFAULT_QUERY", "cafes in Paris")
DEFAULT_LOCATION = os.getenv("DEFAULT_LOCATION", "48.8566,2.3522")
TO_EMAIL = os.getenv("TO_EMAIL", "business@example.com")  # for testing

def main():
    businesses = fetch_business_data(GOOGLE_PLACES_API_KEY, DEFAULT_QUERY, DEFAULT_LOCATION)

    for biz in businesses:
        if not biz["website"]:
            continue
        print(f"Analyzing {biz['name']}...")
        analysis = analyze_website(biz["website"])
        report = generate_report(biz["name"], analysis)
        send_email(TO_EMAIL, report)

if __name__ == "__main__":
    main()
