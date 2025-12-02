import requests
from pydantic import BaseModel, Field
from typing import List

GRAPH_URL = "https://graph.microsoft.com/v1.0"

# -------------------------
# Pydantic Schemas
# -------------------------

class CheckAvailabilityInput(BaseModel):
    date: str = Field(..., description="The date for the meeting, e.g., '2025-12-15'.")
    time: str = Field(..., description="The start time for the meeting in 24-hour format, e.g., '09:00:00'.")
    duration_minutes: int = Field(..., description="Duration of the meeting in minutes, e.g., 60.")

class ScheduleMeetingInput(BaseModel):
    date: str = Field(..., description="The date for the meeting, e.g., '2025-12-15'.")
    time: str = Field(..., description="The start time for the meeting in 24-hour format, e.g., '14:00:00'.")
    duration_minutes: int = Field(..., description="Duration of the meeting in minutes, e.g., 60.")
    attendees: List[str] = Field(..., description="List of attendee email addresses.")
    subject: str = Field(..., description="Meeting subject.")
    

# -------------------------
# Tool Functions
# -------------------------

def check_calendar_availability(data: CheckAvailabilityInput) -> str:
    # Lazy import → prevents auth from loading at module import time
    from auth import auth_manager

    try:
        headers = auth_manager.get_auth_header()

        start_datetime = f"{data.date}T{data.time}"
        duration_seconds = data.duration_minutes * 60

        from datetime import datetime, timedelta
        end_dt = datetime.fromisoformat(start_datetime) + timedelta(seconds=duration_seconds)
        end_datetime = end_dt.isoformat()

        payload = {
            "schedules": ["me@outlook.com"],
            "startTime": {"dateTime": start_datetime, "timeZone": "America/Chicago"},
            "endTime": {"dateTime": end_datetime, "timeZone": "America/Chicago"},
            "availabilityViewInterval": 60
        }

        response = requests.post(
            f"{GRAPH_URL}/me/calendar/getSchedule",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()

        busy = data.get("value", [{}])[0].get("scheduleItems", [])
        if busy:
            return f"Conflict detected at {start_datetime}. Calendar is BUSY."
        return f"Calendar is FREE at {start_datetime}."

    except Exception as e:
        return f"Error checking availability: {e}"


def schedule_new_meeting(data: ScheduleMeetingInput) -> str:
    from auth import auth_manager

    try:
        headers = auth_manager.get_auth_header()

        start_datetime = f"{data.date}T{data.time}"
        duration_seconds = data.duration_minutes * 60

        from datetime import datetime, timedelta
        end_dt = datetime.fromisoformat(start_datetime) + timedelta(seconds=duration_seconds)
        end_datetime = end_dt.isoformat()

        attendees = [{"emailAddress": {"address": a}, "type": "required"} for a in data.attendees]

        payload = {
            "subject": data.subject,
            "start": {"dateTime": start_datetime, "timeZone": "America/Chicago"},
            "end": {"dateTime": end_datetime, "timeZone": "America/Chicago"},
            "attendees": attendees,
            "isOnlineMeeting": True,
            "onlineMeetingProvider": "teamsForBusiness"
        }

        response = requests.post(f"{GRAPH_URL}/me/events", headers=headers, json=payload)
        response.raise_for_status()
        event = response.json()

        return f"Meeting scheduled: {event['subject']} at {event['start']['dateTime']}"

    except Exception as e:
        return f"Error scheduling meeting: {e}"


# Export tools
tools = [check_calendar_availability, schedule_new_meeting]
