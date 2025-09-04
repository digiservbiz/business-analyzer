import requests

def send_to_n8n(webhook_url, data):
    """Sends data to a specified n8n webhook."""
    try:
        # In a real-world scenario, you would use the requests library to send the data.
        # The following line is commented out to avoid dependency issues.
        # response = requests.post(webhook_url, json=data)
        
        # For demonstration purposes, we'll print the data that would be sent.
        print("--- SIMULATING N8N WEBHOOK --- ")
        print(f"Webhook URL: {webhook_url}")
        print("Data sent:")
        print(data)
        print("--- END SIMULATING N8N WEBHOOK ---")
        
        # You can uncomment this line to check the response from your n8n webhook.
        # response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"Error sending data to n8n: {e}")

