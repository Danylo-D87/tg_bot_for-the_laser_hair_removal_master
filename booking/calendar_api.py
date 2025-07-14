import datetime
import json
import os

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

from bot.bot_utils import is_within_working_hours

load_dotenv()

# Константи, налаштуй під свій проект
SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")  # path to JSON key
CALENDAR_ID = os.getenv("CALENDAR_ID")
TIMEZONE = "Europe/Kiev"

# Ініціалізація клієнта
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("calendar", "v3", credentials=credentials)


with open("working_hours.json", "r") as f:
    schedule = json.load(f)


def list_free_slots(specialist="laserepilation", start_iso=None, end_iso=None, duration_minutes=40):
    """
    Retrieves and returns a list of available time slots within a specified date range.

    Args:
        [cite_start]specialist (str): The specialist for whom to find slots (e.g., "laserepilation"). [cite: 16]
        [cite_start]start_iso (str): ISO 8601 formatted datetime string representing the start of the search period. [cite: 16]
        [cite_start]end_iso (str): ISO 8601 formatted datetime string representing the end of the search period. [cite: 16]
        [cite_start]duration_minutes (int): The required duration of each slot in minutes. [cite: 16]

    Returns:
        list: A list of dictionaries, where each dictionary represents a free slot
              with 'start_iso' and 'end_iso' keys.
    """
    if not start_iso or not end_iso:
        return "start_iso та end_iso обов'язкові параметри"

    body = {
        "timeMin": start_iso,
        "timeMax": end_iso,
        "timeZone": TIMEZONE,
        "items": [{"id": CALENDAR_ID}]
    }

    freebusy_result = service.freebusy().query(body=body).execute()
    busy_times = freebusy_result["calendars"][CALENDAR_ID]["busy"]

    busy_intervals = [
        (datetime.datetime.fromisoformat(busy["start"]), datetime.datetime.fromisoformat(busy["end"]))
        for busy in busy_times
    ]

    start_dt = datetime.datetime.fromisoformat(start_iso)
    end_dt = datetime.datetime.fromisoformat(end_iso)

    free_slots = []
    current_start = start_dt

    for busy_start, busy_end in sorted(busy_intervals):
        if current_start + datetime.timedelta(minutes=duration_minutes) <= busy_start:
            slot_end = busy_start
            while current_start + datetime.timedelta(minutes=duration_minutes) <= slot_end:
                slot_finish = current_start + datetime.timedelta(minutes=duration_minutes)
                free_slots.append((
                    current_start.isoformat(),
                    slot_finish.isoformat()
                ))
                current_start = slot_finish
        current_start = max(current_start, busy_end)

    while current_start + datetime.timedelta(minutes=duration_minutes) <= end_dt:
        slot_finish = current_start + datetime.timedelta(minutes=duration_minutes)
        free_slots.append((
            current_start.isoformat(),
            slot_finish.isoformat()
        ))
        current_start = slot_finish

    filtered_slots = [
        (start, end) for start, end in free_slots if is_within_working_hours(start, end, schedule)
    ]

    return [{"start_iso": start, "end_iso": end} for start, end in filtered_slots]


def create_appointment(specialist, start_iso, end_iso, summary, description, attendee_email=None):
    """
    Creates an event (appointment) in the Google Calendar.

    Args:
        [cite_start]specialist (str): The specialist for whom the appointment is booked (e.g., "laserepilation"). [cite: 17]
        [cite_start]start_iso (str): ISO 8601 formatted datetime string for the start of the event. [cite: 17]
        [cite_start]end_iso (str): ISO 8601 formatted datetime string for the end of the event. [cite: 17]
        [cite_start]summary (str): The title of the event. [cite: 17]
        [cite_start]description (str): A detailed description of the event. [cite: 17]
        [cite_start]attendee_email (str, optional): The email address of an attendee to be added to the event. [cite: 17]

    Returns:
        dict: The created event resource as returned by the Google Calendar API.
    """
    event = {
        "summary": summary,
        "description": description + attendee_email if attendee_email else description,
        "start": {
            "dateTime": start_iso,
            "timeZone": TIMEZONE,
        },
        "end": {
            "dateTime": end_iso,
            "timeZone": TIMEZONE,
        },
    }
    # if attendee_email:
    #     event["attendees"] = [{"email": attendee_email}]

    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return created_event
