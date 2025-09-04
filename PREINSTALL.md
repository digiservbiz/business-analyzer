# Pre-installation Guide for Business Outreach Tool

This document outlines the necessary prerequisites and setup steps required before installing the Business Outreach Tool.

## 1. System Prerequisites

Ensure you have the following software installed on your system:

- **Python 3.8 or higher:** You can download Python from [python.org](https://python.org).
- **pip:** Python's package installer. It usually comes with Python installations.
- **git:** For cloning the project repository. You can download it from [git-scm.com](https://git-scm.com/).

## 2. Obtain API Keys

The application uses the Google Maps API to fetch business data. You will need to obtain a valid API key.

- **Google Maps API Key:**
  1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
  2.  Create a new project (or select an existing one).
  3.  Enable the **Places API**.
  4.  Go to 'Credentials' and create a new API key.
  5.  It is highly recommended to restrict your API key to prevent unauthorized use. You can restrict it to the IP addresses of your servers.

## 3. Clone the Repository

Once you have the prerequisites, clone the project repository to your local machine using the following command:

```bash
git clone https://github.com/digiservbiz/business-analyzer.git
cd business-analyzer
```

After completing these steps, you are ready to proceed with the installation instructions in the `POSTINSTALL.md` file.
