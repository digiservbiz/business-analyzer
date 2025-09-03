from scraper.google_scraper import fetch_business_data
from analyzer.website_analyzer import analyze_website
from reports.report_generator import generate_report
from outreach.email_sender import send_email

businesses = fetch_business_data("YOUR_GOOGLE_API_KEY", "cafes in Paris", "48.8566,2.3522")

for biz in businesses:
    if not biz["website"]:
        continue
    analysis = analyze_website(biz["website"])
    report = generate_report(biz["name"], analysis)
    send_email("business@example.com", report)
