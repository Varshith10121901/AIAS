import os
import requests
import secrets
from datetime import datetime, timedelta
from config import Config


class ZoomService:
    """Service to handle Zoom meeting scheduling and API authentication."""

    @staticmethod
    def get_access_token():
        """Retrieve access token using Server-to-Server OAuth credentials."""
        account_id = Config.ZOOM_ACCOUNT_ID
        client_id = Config.ZOOM_CLIENT_ID
        client_secret = Config.ZOOM_CLIENT_SECRET

        if not account_id or not client_id or not client_secret:
            raise ValueError("Missing Zoom API credentials in Config.")

        # Support both raw account ID and pre-constructed OAuth endpoint paths
        if not account_id.startswith("/"):
            url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={account_id}"
        else:
            url = f"https://zoom.us{account_id}"

        response = requests.post(url, auth=(client_id, client_secret), timeout=15)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            raise Exception(f"Zoom Auth Failed ({response.status_code}): {response.text}")

    @staticmethod
    def create_meeting(start_time_dt=None, timezone="Asia/Kolkata"):
        """
        Schedule a unique Zoom meeting.
        If start_time_dt is None, defaults to 72 hours from now in UTC.
        """
        try:
            token = ZoomService.get_access_token()
            url = "https://api.zoom.us/v2/users/me/meetings"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            if start_time_dt is None:
                start_time_dt = datetime.utcnow() + timedelta(hours=72)
                timezone = "UTC"

            # Format start time: Zoom expects %Y-%m-%dT%H:%M:%SZ for UTC, else %Y-%m-%dT%H:%M:%S
            if timezone == "UTC":
                start_time_str = start_time_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                start_time_str = start_time_dt.strftime("%Y-%m-%dT%H:%M:%S")

            meeting_details = {
                "topic": "AIAS Client Discovery Call",
                "type": 2,  # Scheduled, unique meeting
                "start_time": start_time_str,
                "duration": 30,  # 30 minutes
                "timezone": timezone,
                "settings": {
                    "host_video": True,
                    "participant_video": True,
                    "join_before_host": False,
                    "mute_upon_entry": True
                }
            }

            response = requests.post(url, headers=headers, json=meeting_details, timeout=15)
            if response.status_code == 201:
                return response.json().get("join_url")
            else:
                raise Exception(f"Zoom Meeting Creation Failed ({response.status_code}): {response.text}")

        except Exception as e:
            # Return None on failure so the system knows the meeting link is pending
            print(f"[ZoomService Warning] Could not create Zoom meeting via API: {str(e)}")
            return None
