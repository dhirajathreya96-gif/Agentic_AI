import datetime as dt
from langchain.tools import tool

# This is a Pydantic model for structured output validation (Best Practice)
from pydantic import BaseModel, Field

# --- Tool 1: Check Availability ---
class CheckAvailabilityInput(BaseModel):
    """Input schema for checking calendar availability."""
    start_time: str = Field(description="The start time for the check, e.g., '2025-12-01 10:00:00'.")
    duration_minutes: int = Field(description="The required duration in minutes, e.g., 30 or 60.")

@tool(args_schema=CheckAvailabilityInput)
def check_calendar_availability(start_time: str, duration_minutes: int) -> str:
    """
    Checks the user's calendar to see if they are free at the specified time 
    for the given duration. Returns a human-readable availability report.
    """
    # Simulate a busy period
    busy_start = dt.datetime(2025, 12, 1, 10, 30, 0)
    busy_end = dt.datetime(2025, 12, 1, 11, 30, 0)

    try:
        requested_start = dt.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        requested_end = requested_start + dt.timedelta(minutes=duration_minutes)
    except ValueError:
        return "ERROR: Time format must be YYYY-MM-DD HH:MM:SS. Please ask the user to clarify the date/time."

    if requested_start < busy_end and requested_end > busy_start:
        return f"The calendar is **BUSY** from {busy_start.strftime('%H:%M')} to {busy_end.strftime('%H:%M')} on Dec 1st. You are not free at {requested_start.strftime('%H:%M')}."
    else:
        return f"The calendar is **FREE** at the requested time: {requested_start.strftime('%Y-%m-%d %H:%M')}, for {duration_minutes} minutes."

# --- Tool 2: Schedule Meeting ---
class ScheduleMeetingInput(BaseModel):
    """Input schema for scheduling a new meeting."""
    attendee: str = Field(description="The name of the main person to schedule the meeting with.")
    start_time: str = Field(description="The start time for the meeting, e.g., '2025-12-02 14:00:00'.")
    duration_minutes: int = Field(description="The meeting duration in minutes.")
    title: str = Field(description="A concise, descriptive title for the meeting.")

@tool(args_schema=ScheduleMeetingInput)
def schedule_new_meeting(attendee: str, start_time: str, duration_minutes: int, title: str) -> str:
    """
    Schedules a new meeting with the specified attendee, time, duration, and title. 
    Returns a confirmation message.
    """
    # In a real app, this sends an API call to create the calendar event.
    return f"SUCCESS: Scheduled a {duration_minutes}-minute meeting with **{attendee}** titled '{title}' on **{start_time}**."
    