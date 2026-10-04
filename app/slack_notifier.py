import os
import requests


SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack_alert(message):
    if not SLACK_WEBHOOK_URL:
        return {
            "sent": False,
            "reason": "SLACK_WEBHOOK_URL not configured"
        }

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": message},
            timeout=5
        )

        response.raise_for_status()

        return {
            "sent": True
        }

    except Exception as error:
        return {
            "sent": False,
            "error": str(error)
        }