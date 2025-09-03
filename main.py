
import argparse
import os
import sqlite3
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from reports.report_generator import generate_report
from outreach.email_sender import send_email
from database.schema import setup_database

TO_EMAIL = os.getenv("TO_EMAIL", "business@example.com")  # for testing

def add_template(name, subject, body):
    """Adds a new email template to the database using sqlite3."""
    try:
        conn = sqlite3.connect('businesses.db')
        c = conn.cursor()
        c.execute("INSERT INTO email_templates (name, subject, body) VALUES (?, ?, ?)",
                  (name, subject, body))
        conn.commit()
        conn.close()
        print(f"Template ''{name}'' added successfully.")
    except sqlite3.IntegrityError:
        print(f"Error: A template with the name ''{name}'' already exists.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Business Analyzer and Outreach Tool.")
    parser.add_argument("--setup-db", action="store_true", help="Setup the database.")
    parser.add_argument("--add-template", action="store_true", help="Add a new email template.")
    parser.add_argument("--name", help="Name of the template")
    parser.add_argument("--subject", help="Subject of the email")
    parser.add_argument("--body", help="Body of the email")

    args = parser.parse_args()

    if args.setup_db:
        print("Setting up database...")
        setup_database()
        print("Database setup complete.")
    elif args.add_template:
        if not (args.name and args.subject and args.body):
            print("Error: --name, --subject, and --body are required for adding a template.")
            return
        add_template(args.name, args.subject, args.body)
    else:
        print("No action specified. Use --setup-db or --add-template.")

if __name__ == "__main__":
    main()
