import sqlite3

def add_template(name, subject, body):
    """Adds a new email template to the database."""
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

def get_all_templates():
    """Fetches all email templates from the database."""
    try:
        conn = sqlite3.connect('businesses.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT name, subject, body FROM email_templates")
        templates = c.fetchall()
        conn.close()
        return templates
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
