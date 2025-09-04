
import sqlite3

def seed_database():
    conn = sqlite3.connect('businesses.db')
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO email_templates (name, subject, body)
            VALUES (?, ?, ?)
        """, (
            'initial_outreach',
            'Connecting with {business_name}',
            "Hello {business_name}, we admire your work and would love to explore how we can collaborate. Please let us know if you're interested in a brief chat."
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        print("Template already exists.")
    finally:
        conn.close()

if __name__ == '__main__':
    print("Seeding database with initial data...")
    seed_database()
    print("Done.")
