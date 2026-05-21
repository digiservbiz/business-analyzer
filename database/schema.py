import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'businesses.db')

def setup_database(db_path=None):
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY,
            domain TEXT UNIQUE NOT NULL,
            keywords TEXT,
            industry TEXT,
            location TEXT,
            asking_price REAL DEFAULT 0,
            status TEXT DEFAULT 'available',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS domain_pitches (
            id INTEGER PRIMARY KEY,
            domain_id INTEGER NOT NULL,
            business_id INTEGER NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (domain_id) REFERENCES domains(id) ON DELETE CASCADE,
            FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE,
            UNIQUE(domain_id, business_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS domain_contacts (
            id INTEGER PRIMARY KEY,
            domain_id INTEGER NOT NULL,
            business_id INTEGER,
            name TEXT,
            title TEXT,
            email TEXT,
            linkedin_url TEXT,
            source TEXT DEFAULT 'apollo',
            found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pitched INTEGER DEFAULT 0,
            FOREIGN KEY (domain_id) REFERENCES domains(id) ON DELETE CASCADE,
            FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE SET NULL
        )
    ''')
    # Migrate domain_contacts: add pitched_at and followup_sent if missing
    for _sql in [
        "ALTER TABLE domain_contacts ADD COLUMN pitched_at TIMESTAMP",
        "ALTER TABLE domain_contacts ADD COLUMN followup_sent INTEGER DEFAULT 0",
    ]:
        try:
            c.execute(_sql)
        except sqlite3.OperationalError:
            pass  # column already exists
    # Migrate domain_contacts: add lead_score, replied, replied_at, reply_draft
    for _sql in [
        "ALTER TABLE domain_contacts ADD COLUMN lead_score INTEGER DEFAULT 0",
        "ALTER TABLE domain_contacts ADD COLUMN replied INTEGER DEFAULT 0",
        "ALTER TABLE domain_contacts ADD COLUMN replied_at TIMESTAMP",
        "ALTER TABLE domain_contacts ADD COLUMN reply_draft TEXT",
    ]:
        try:
            c.execute(_sql)
        except sqlite3.OperationalError:
            pass  # column already exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS campaign_runs (
            id INTEGER PRIMARY KEY,
            domain_id INTEGER NOT NULL,
            domain TEXT,
            businesses_fetched INTEGER DEFAULT 0,
            weak_website_count INTEGER DEFAULT 0,
            contacts_found INTEGER DEFAULT 0,
            emails_sent INTEGER DEFAULT 0,
            errors TEXT,
            ran_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (domain_id) REFERENCES domains(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("Setting up database and creating tables...")
    setup_database()
    print("Done.")
