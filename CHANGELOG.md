# Changelog

All notable changes to this project will be documented in this file.

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
