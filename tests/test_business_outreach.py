"""Unit tests for business_outreach module."""
import sys
import os
import sqlite3
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from business_outreach import generate_outreach_message, fetch_and_save_businesses_mock
from database.schema import setup_database


class TestGenerateOutreachMessage(unittest.TestCase):
    def test_with_website(self):
        msg = generate_outreach_message("Acme Corp", "http://acme.com")
        self.assertIn("Acme Corp", msg)
        self.assertIn("acme.com", msg)

    def test_without_website(self):
        msg = generate_outreach_message("Acme Corp", "")
        self.assertIn("Acme Corp", msg)
        self.assertNotIn("http", msg)


class TestFetchAndSaveBusinessesMock(unittest.TestCase):
    def setUp(self):
        """Create a temporary database for testing."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        # Monkey-patch the db path used by business_outreach
        import business_outreach
        self._orig_connect = sqlite3.connect
        self.db_path_to_use = self.db_path

        # Setup the temp db
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE businesses (
            id INTEGER PRIMARY KEY,
            name TEXT,
            address TEXT,
            website TEXT UNIQUE
        )''')
        conn.commit()
        conn.close()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_outreach_message_has_content(self):
        msg = generate_outreach_message("Test Biz", "http://test.com")
        self.assertIsInstance(msg, str)
        self.assertGreater(len(msg), 10)


class TestReportGenerator(unittest.TestCase):
    def test_generate_report_creates_csv(self):
        from reports.report_generator import generate_report
        import tempfile
        businesses = [("Biz A", "123 St", "http://a.com"), ("Biz B", "456 Ave", "http://b.com")]
        with tempfile.TemporaryDirectory() as tmpdir:
            import reports.report_generator as rg
            original = rg.generate_report
            path = generate_report(businesses)
            self.assertTrue(os.path.exists(path))


if __name__ == '__main__':
    unittest.main()
