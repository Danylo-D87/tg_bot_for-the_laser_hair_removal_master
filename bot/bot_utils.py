from datetime import datetime
import re
from zoneinfo import ZoneInfo


EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")


def format_slots(slots):
    msg = "Ось доступні дати та часи для запису:\n"
    for i, slot in enumerate(slots, start=1):
        dt = datetime.fromisoformat(slot['start_iso'])
        msg += f"{i}. {dt.strftime('%d.%m.%Y о %H:%M')}\n"
    msg += "\nНапишіть номер зручного слоту для бронювання."
    return msg


def parse_date_range(text):
    pattern = r"з\s+(\d{1,2})\.(\d{1,2})\s+по\s+(\d{1,2})\.(\d{1,2})"
    match = re.search(pattern, text.lower())
    if not match:
        return None

    day1, month1, day2, month2 = map(int, match.groups())
    year = datetime.now().year
    try:
        start = datetime(year, month1, day1)
        end = datetime(year, month2, day2)
    except ValueError:
        return None

    return (start, end) if start < end else None


def is_within_working_hours(start_iso, end_iso, config):
    tz = ZoneInfo(config.get("timezone", "Europe/Kyiv"))
    start_dt = datetime.fromisoformat(start_iso).astimezone(tz)
    end_dt = datetime.fromisoformat(end_iso).astimezone(tz)

    workday_start_time = datetime.strptime(config["workday_start"], "%H:%M").time()
    workday_end_time = datetime.strptime(config["workday_end"], "%H:%M").time()
    break_start_time = datetime.strptime(config["break_start"], "%H:%M").time()
    break_end_time = datetime.strptime(config["break_end"], "%H:%M").time()

    # Тепер задаємо tzinfo для datetime, щоб вони були aware
    workday_start = datetime.combine(start_dt.date(), workday_start_time, tzinfo=tz)
    workday_end = datetime.combine(start_dt.date(), workday_end_time, tzinfo=tz)
    break_start = datetime.combine(start_dt.date(), break_start_time, tzinfo=tz)
    break_end = datetime.combine(start_dt.date(), break_end_time, tzinfo=tz)

    if start_dt < workday_start or end_dt > workday_end:
        return False

    if start_dt < break_end and end_dt > break_start:
        return False

    return True

