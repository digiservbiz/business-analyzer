
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY,
            name TEXT,
            address TEXT,
            website TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("Setting up database and creating tables...")
    setup_database()
    print("Done.")
