import requests


def send_to_n8n(webhook_url, data):
    """
    Sends data to a specified n8n webhook.

    Returns:
        True  — request succeeded (2xx response)
        False — request failed (network error, timeout, or bad status)
    """
    try:
        response = requests.post(webhook_url, json=data, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.Timeout:
        print("n8n webhook request timed out.")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"n8n webhook connection error: {e}")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"n8n webhook HTTP error: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"n8n webhook error: {e}")
        return False
