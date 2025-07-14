import os
from datetime import datetime, timezone, timedelta

import telebot
from dotenv import load_dotenv

from llm.llm_answer import get_llm_answer
from llm.llm_detect_booking_intent import detect_booking_intent
from booking.calendar_api import list_free_slots, create_appointment
from .bot_utils import parse_date_range, format_slots, EMAIL_REGEX


load_dotenv()
bot = telebot.TeleBot(token=os.getenv("TOKEN"))

user_status = {}
user_temp_data = {}

MAX_MESSAGE_LENGTH = 4000

def send_long_message(chat_id, text):
    """
        Sends a potentially long text message to a specified chat by splitting it into
        multiple messages if it exceeds the Telegram message length limit.
    """
    for i in range(0, len(text), MAX_MESSAGE_LENGTH):
        bot.send_message(chat_id, text[i:i+MAX_MESSAGE_LENGTH])


@bot.message_handler(commands=["start"])
def start(message):
    """
        Handles the /start command.
        Resets the user's status to 'chat' and sends a welcome message.
    """
    user_status[message.from_user.id] = "chat"
    bot.send_message(message.chat.id, "Привіт! Я асистент студії LaserHouse, Чим можу допомогти?")


@bot.message_handler(func=lambda m: user_status.get(m.from_user.id, "chat") == "chat")
def handle_message(message):
    user_id = message.from_user.id

    if detect_booking_intent(message.text):
        user_status[user_id] = "slot_selection"
        bot.send_message(
            message.chat.id,
            "Супер! Давайте підберемо зручну для вас дату, вкажіть з якої дати до якої ви б хотіли переглянути вільні місця.\nУ такому форматі: з 15.07 по 20.07",
        )

    else:
        reply = get_llm_answer(message.text)
        bot.send_message(message.chat.id, reply)


@bot.message_handler(func=lambda m: user_status.get(m.from_user.id) == "slot_selection")
def handle_booking_slot_selection(message):
    """
        Handles general chat messages when the user's status is 'chat'.
        Detects booking intent or uses an LLM to generate a reply.
    """
    user_id = message.from_user.id

    date_range = parse_date_range(message.text)
    if not date_range:
        bot.send_message(
            message.chat.id,
            "Будь ласка, введіть діапазон ще раз у форматі: з 15.07 по 20.07",
        )
        return

    start_date, end_date = date_range
    kyiv_tz = timezone(timedelta(hours=3))
    start_date = start_date.replace(tzinfo=kyiv_tz)
    end_date = end_date.replace(tzinfo=kyiv_tz)
    slots = list_free_slots(
        start_iso=start_date.isoformat(),
        end_iso=end_date.isoformat()
    )

    if not slots:
        bot.send_message(
            message.chat.id,
            "На жаль, немає вільних слотів у вказаний період. Спробуйте інший діапазон.",
        )
        return

    user_temp_data[user_id] = {"slots": slots}

    reply = format_slots(slots) + "Напишіть номер дати, котра вас влаштовує"
    send_long_message(message.chat.id, reply)
    user_status[user_id] = "slot_confirmation"


@bot.message_handler(func=lambda m: user_status.get(m.from_user.id) == "slot_confirmation")
def handle_booking_slot_confirmation(message):
    user_id = message.from_user.id
    user_data = user_temp_data.get(user_id)

    if not user_data or "slots" not in user_data:
        bot.send_message(message.chat.id, "Сталася помилка, будь ласка, введіть діапазон дат знову.")
        user_status[user_id] = "slot_selection"
        return

    try:
        choice = int(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, "Будь ласка, введіть номер дати з переліку дат.")
        bot.send_message(message.chat.id, format_slots(user_data["slots"]))
        return

    slots = user_data["slots"]
    if choice < 1 or choice > len(slots):
        bot.send_message(message.chat.id, "Номер поза межами доступних варіантів. Спробуйте ще раз.")
        return

    selected_slot = slots[choice - 1]
    user_temp_data[user_id]["selected_slot"] = selected_slot
    user_status[user_id] = "booking_confirmation"
    bot.send_message(
        message.chat.id,
        "Дякую! Тепер, будь ласка, введіть ваш email для підтвердження запису, та отримання запрошення-перепустки.",
    )


@bot.message_handler(func=lambda m: user_status.get(m.from_user.id) == "booking_confirmation")
def handle_booking_email(message):
    user_id = message.from_user.id
    email = message.text.strip()

    if not EMAIL_REGEX.match(email):
        bot.send_message(message.chat.id, "Введіть, будь ласка, коректний email.")
        return

    selected_slot = user_temp_data[user_id].get("selected_slot")
    if not selected_slot:
        bot.send_message(message.chat.id, "Сталася помилка. Почнемо спочатку. Введіть діапазон дат.")
        user_status[user_id] = "slot_selection"
        return

    try:
        create_appointment(
            specialist="laserepilation",
            start_iso=selected_slot["start_iso"],
            end_iso=selected_slot["end_iso"],
            summary="Запис на лазерну епіляцію",
            description=f"Клієнт Telegram user_id: {user_id}",
            attendee_email=email
        )

    except Exception as e:
        bot.send_message(message.chat.id, "Сталася помилка при бронюванні. Спробуйте пізніше.")
        user_status[user_id] = "chat"
        user_temp_data.pop(user_id, None)
        return


    dt = datetime.fromisoformat(selected_slot["start_iso"])
    bot.send_message(message.chat.id, f"Запис підтверджено ✅ Чекаємо вас {dt.strftime('%d.%m.%Y о %H:%M')}")
    user_status[user_id] = "chat"
    user_temp_data.pop(user_id, None)


def run_bot():
    print("🤖 Бот працює")
    bot.infinity_polling()
