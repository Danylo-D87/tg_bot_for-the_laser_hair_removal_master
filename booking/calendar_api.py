import datetime
import json
import os

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

from bot_utils import is_within_working_hours

load_dotenv()

# Константи, налаштуй під свій проект
SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")  # шлях до JSON ключа
CALENDAR_ID = os.getenv("CALENDAR_ID")  # email календаря майстра
TIMEZONE = "Europe/Kiev"

# Ініціалізація клієнта
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("calendar", "v3", credentials=credentials)


# Зчитуємо конфіг
with open("working_hours.json", "r") as f:
    schedule = json.load(f)


def list_free_slots(specialist="laserepilation", start_iso=None, end_iso=None, duration_minutes=40):
    """
    Повертає список вільних слотів у заданому діапазоні часу.
    Параметри:
    - start_iso: ISO datetime початку періоду (наприклад, "2025-07-15T09:00:00+03:00")
    - end_iso: ISO datetime кінця періоду
    - duration_minutes: тривалість слоту в хвилинах

    Повертає список кортежів (start_iso, end_iso) вільних слотів.
    """
    if not start_iso or not end_iso:
        return "start_iso та end_iso обов'язкові параметри"

    # Формат запиту для freebusy
    body = {
        "timeMin": start_iso,
        "timeMax": end_iso,
        "timeZone": TIMEZONE,
        "items": [{"id": CALENDAR_ID}]
    }

    freebusy_result = service.freebusy().query(body=body).execute()
    busy_times = freebusy_result["calendars"][CALENDAR_ID]["busy"]

    # Перетворимо busy у datetime об"єкти
    busy_intervals = [
        (datetime.datetime.fromisoformat(busy["start"]), datetime.datetime.fromisoformat(busy["end"]))
        for busy in busy_times
    ]

    start_dt = datetime.datetime.fromisoformat(start_iso)
    end_dt = datetime.datetime.fromisoformat(end_iso)

    # Знаходимо вільні інтервали
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

    # Перевіряємо останній вільний інтервал після останнього busy
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
    Створює подію у Google Calendar.
    Параметри:
    - specialist: рядок (в ТЗ – "laserepilation")
    - start_iso: ISO datetime початку події
    - end_iso: ISO datetime кінця події
    - summary: заголовок події (наприклад, "Запис клієнта")
    - description: опис події
    - attendee_email: email клієнта (опціонально)

    Повертає створену подію (dict).
    """
    event = {
        "summary": summary,
        "description": description,
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
    print("Created event:", created_event)
    return created_event
