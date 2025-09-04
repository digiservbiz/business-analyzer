# Post-installation Guide for Business Outreach Tool

This guide provides instructions for setting up and running the Business Outreach Tool after completing the pre-installation steps.

## 1. Set Up a Virtual Environment

It is recommended to use a virtual environment to manage project dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

This will create and activate a virtual environment in the `.venv` directory.

## 2. Install Dependencies

Install the required Python packages using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

## 3. Configure Environment Variables

The application uses a `.env` file to manage environment variables. Create a `.env` file in the root of the project directory and add the following variables:

```
# Your Google Maps API key
GOOGLE_MAPS_API_KEY='YOUR_GOOGLE_MAPS_API_KEY'

# Port for the Flask application
PORT=8081

# Optional: Set to 'invalid_key' to use mocked data for testing
# GOOGLE_MAPS_API_KEY='invalid_key'
```

Replace `'YOUR_GOOGLE_MAPS_API_KEY'` with the API key you obtained in the pre-installation steps.

## 4. Run the Application

Once the dependencies are installed and the environment variables are configured, you can run the application.

```bash
.venv/bin/python app.py
```

The application will be accessible at `http://127.0.0.1:8081`.

## 5. Using the Application

1.  **Fetch Businesses:**
    *   Navigate to the home page.
    *   Enter a search query (e.g., "restaurants in New York").
    *   Provide a location (latitude and longitude, e.g., "40.7128,-74.0060").
    *   Click the "Fetch Businesses" button to populate the database with business information.

2.  **View and Manage Data:**
    *   The business table will display the fetched data.
    *   You can view, edit, or delete business entries.

3.  **Generate Reports:**
    *   Click the "Generate Report" button to download a CSV file of the current business data.
