
import sqlite3

def setup_database():
    conn = sqlite3.connect('businesses.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS email_templates (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("Setting up database and creating email_templates table...")
    setup_database()
    print("Done.")
