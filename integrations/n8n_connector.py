import requests

def send_to_n8n(webhook_url, data):
    """Sends data to a specified n8n webhook."""
    try:
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"Error sending data to n8n: {e}")

