import os

import telebot
from dotenv import load_dotenv

from llm.llm_answer import get_llm_answer
from llm.llm_detect_booking_intent import detect_booking_intent


load_dotenv()
bot = telebot.TeleBot(token=os.getenv("TOKEN"))


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привіт! Я асистент студії LaserHouse, Чим можу допомогти?")


@bot.message_handler(func=lambda m: True)
def handle_message(message):

    if detect_booking_intent(message.text):
        bot.send_message(message.chat.id, "Супер! Давайте підберемо зручну для вас дату:")
        # TODO booking
    else:
        reply = get_llm_answer(message.text)
        bot.send_message(message.chat.id, reply)


print("🤖 Бот працює")
bot.infinity_polling()

