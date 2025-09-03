# Business Outreach and Analysis Tool

This project is a command-line application designed to streamline business outreach
by managing email templates and sending emails. It also includes functionalities
for database management and report generation.

## Getting Started

These instructions will get you a copy of the project up and running on your
local machine for development and testing purposes.

### Prerequisites

* Python 3.x
* `pip` for installing Python packages

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/business-analyzer.git
    cd business-analyzer
    ```

2.  **Install dependencies:**

    This project has no external dependencies listed in `requirements.txt`.

### Database Setup

Before running the application, you need to set up the SQLite database. The
database will store business information and email templates.

To set up the database, run the following command from the project's root
directory:

```bash
python3 main.py --setup-db
```

This command will create a `businesses.db` file in the project's root directory
with the necessary tables.

## Usage

The primary functionalities of this tool are managed through the command line.

### Adding an Email Template

You can add new email templates to the database. A template consists of a name,
a subject, and a body.

To add a new template, use the `--add-template` flag along with the `--name`,
`--subject`, and `--body` arguments:

```bash
python3 main.py --add-template \
    --name "My First Template" \
    --subject "Following Up" \
    --body "This is a test email body."
```

If a template with the same name already exists, the application will return an
error.

## Project Structure

The project is organized into the following directories and files:

```
.
├── main.py
├── database/
│   ├── __init__.py
│   ├── schema.py
│   └── manage_templates.py
├── outreach/
│   ├── __init__.py
│   └── email_sender.py
└── reports/
    ├── __init__.py
    └── report_generator.py
```

*   **`main.py`**: The entry point for the command-line interface (CLI). It
    handles argument parsing and calls the appropriate functions.

*   **`database/`**: Contains modules related to database interactions.
    *   **`schema.py`**: Defines the database schema and sets up the tables.
    *   **`manage_templates.py`**: Provides functions for managing email
        templates.

*   **`outreach/`**: Contains modules for outreach-related tasks.
    *   **`email_sender.py`**: Manages the process of sending emails.

*   **`reports/`**: Contains modules for generating reports.
    *   **`report_generator.py`**: Generates reports based on the data in the
        database.

## Modules

### `main.py`

The main driver of the application. It uses `argparse` to handle command-line
arguments and orchestrates the application's workflow.

### `database/schema.py`

This module is responsible for creating the database and its tables. The `setup_database()`
function will connect to the SQLite database file (`businesses.db`) and execute the
`CREATE TABLE` statements for `businesses` and `email_templates`.

### `database/manage_templates.py`

This module provides functionality for managing email templates, including adding,
deleting, and updating templates in the database.

### `outreach/email_sender.py`

This module handles the email sending logic. It retrieves business information and
email templates from the database to send personalized emails.

### `reports/report_generator.py`

This module generates reports from the collected data. The reports can provide
insights into outreach campaigns, such as the number of emails sent and the
engagement rates.

## Contributing

Contributions are welcome! If you have a suggestion or find a bug, please open
an issue to discuss it.

When contributing to this repository, please first discuss the change you wish
to make via an issue, email, or any other method with the owners of this
repository before making a change.

## License

This project is licensed under the MIT License - see the `LICENSE.md` file for
details.
