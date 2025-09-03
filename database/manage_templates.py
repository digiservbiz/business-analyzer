
import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.schema import EmailTemplate, Base

# Database setup
engine = create_engine('sqlite:///businesses.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

def add_template(name, subject, body):
    """Adds a new email template to the database."""
    session = DBSession()
    new_template = EmailTemplate(name=name, subject=subject, body=body)
    session.add(new_template)
    session.commit()
    session.close()
    print(f"Template ''{name}'' added successfully.")

def main():
    parser = argparse.ArgumentParser(description="Manage email templates.")
    parser.add_argument("action", choices=["add"], help="Action to perform")
    parser.add_argument("--name", help="Name of the template")
    parser.add_argument("--subject", help="Subject of the email")
    parser.add_argument("--body", help="Body of the email")

    args = parser.parse_args()

    if args.action == "add":
        if not (args.name and args.subject and args.body):
            print("Error: --name, --subject, and --body are required for adding a template.")
            return
        add_template(args.name, args.subject, args.body)

if __name__ == '__main__':
    main()
