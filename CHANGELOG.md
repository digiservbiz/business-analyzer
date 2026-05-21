# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-05-20

### Security
- Removed hardcoded Flask secret key — now loaded from FLASK_SECRET_KEY env var
- Added input sanitization for all form inputs
- Added .gitignore to prevent committing .env and database files

### Fixed
- Fixed `conn` NameError before assignment in `email_sender.py`
- Fixed businesses being deleted on every fetch — now uses upsert (ON CONFLICT DO UPDATE)
- Fixed double single-quotes in template name f-strings
- Fixed `generate_report_route` to use `get_db_connection()` helper consistently

### Added
- Edit and Delete business functionality (UI + backend routes)
- Unit tests in `tests/` directory
- `python-dotenv` added to requirements.txt
- Centralized `DB_PATH` constant in `database/schema.py`

## [1.1.0] - 2024-05-24

### Added

- Integration with n8n to allow sending business data to a webhook.
- New `/send_to_n8n` route in `app.py` to handle the webhook request.
- Updated `index.html` with a form to input the n8n webhook URL and trigger the data sending.
- Enabled the `n8n_connector.py` to send real HTTP requests.

## [1.0.0] - 2024-05-24

### Added

- Initial release of the Business Outreach Tool.
- Core functionality for fetching business data using the Google Maps API.
- SQLite database for storing business information.
- Web interface with a table to display business data.
- Ability to generate and download a CSV report of the business data.

### Fixed

- Business table is now visible by default.
- The app now correctly uses mocked data when the API key is set to 'invalid_key'.
- Resolved an issue where the database was being cleared due to an invalid API key.

### Changed

- Updated the `index.html` file to ensure the business table is always displayed.
- Modified `business_outreach.py` to handle the `invalid_key` case for testing.
