import sqlite3


def add_template(name, subject, body):
    """Adds a new email template to the database."""
    conn = None
    try:
        conn = sqlite3.connect('businesses.db')
        c = conn.cursor()
        c.execute("INSERT INTO email_templates (name, subject, body) VALUES (?, ?, ?)",
                  (name, subject, body))
        conn.commit()
        print(f"Template '{name}' added successfully.")
    except sqlite3.IntegrityError:
        print(f"Error: A template with the name '{name}' already exists.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


def update_template(template_id, subject, body):
    """Updates subject and body of an existing template by ID."""
    conn = None
    try:
        conn = sqlite3.connect('businesses.db')
        conn.execute(
            "UPDATE email_templates SET subject=?, body=? WHERE id=?",
            (subject, body, template_id)
        )
        conn.commit()
        print(f"Template {template_id} updated.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


def delete_template(template_id):
    """Deletes a template by ID."""
    conn = None
    try:
        conn = sqlite3.connect('businesses.db')
        conn.execute("DELETE FROM email_templates WHERE id=?", (template_id,))
        conn.commit()
        print(f"Template {template_id} deleted.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


def get_all_templates():
    """Fetches all email templates from the database."""
    conn = None
    try:
        conn = sqlite3.connect('businesses.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, name, subject, body FROM email_templates")
        templates = c.fetchall()
        return templates
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()
