
import argparse
import os
import sqlite3
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from reports.report_generator import generate_report
from outreach.email_sender import send_email, get_email_template
from database.schema import setup_database
from database.manage_templates import add_template
from business_outreach import fetch_and_save_businesses

TO_EMAIL = os.getenv("TO_EMAIL", "business@example.com")  # for testing

def main():
    parser = argparse.ArgumentParser(description="Business Analyzer and Outreach Tool.")
    parser.add_argument("--setup-db", action="store_true", help="Setup the database.")
    parser.add_argument("--fetch-businesses", action="store_true", help="Fetch businesses from Google Maps.")
    parser.add_argument("--query", help="Query for fetching businesses (e.g., 'restaurants in New York').")
    parser.add_argument("--location", help="Location for fetching businesses (e.g., '40.7128,-74.0060').")
    parser.add_argument("--add-template", action="store_true", help="Add a new email template.")
    parser.add_argument("--name", help="Name of the template")
    parser.add_argument("--subject", help="Subject of the email")
    parser.add_argument("--body", help="Body of the email")
    parser.add_argument("--send-outreach", action="store_true", help="Send outreach emails.")
    parser.add_argument("--template-name", help="Name of the email template to use for outreach.")
    parser.add_argument("--generate-report", action="store_true", help="Generate a report of businesses.")

    args = parser.parse_args()

    if args.setup_db:
        print("Setting up database...")
        setup_database()
        print("Database setup complete.")
    elif args.fetch_businesses:
        if not (args.query and args.location):
            print("Error: --query and --location are required for fetching businesses.")
            return
        fetch_and_save_businesses(args.query, args.location)
    elif args.add_template:
        if not (args.name and args.subject and args.body):
            print("Error: --name, --subject, and --body are required for adding a template.")
            return
        add_template(args.name, args.subject, args.body)
    elif args.send_outreach:
        template = get_email_template(args.template_name) if args.template_name else get_email_template()
        if not template:
            print("No email templates found. Please add a template first.")
            return

        conn = sqlite3.connect('businesses.db')
        c = conn.cursor()
        c.execute("SELECT name, website FROM businesses")
        businesses = c.fetchall()
        conn.close()

        for business_name, website in businesses:
            # In a real-world scenario, you'd have the business's email.
            # We'll use a placeholder for now.
            print(f"Sending outreach to {business_name}...")
            send_email(TO_EMAIL, template['subject'], template['body'])
        print("Outreach complete.")
    elif args.generate_report:
        conn = sqlite3.connect('businesses.db')
        c = conn.cursor()
        c.execute("SELECT name, address, website FROM businesses")
        businesses = c.fetchall()
        conn.close()
        generate_report(businesses)
        print("Report generated successfully.")
    else:
        print("No action specified. Use --help for options.")

if __name__ == "__main__":
    main()
