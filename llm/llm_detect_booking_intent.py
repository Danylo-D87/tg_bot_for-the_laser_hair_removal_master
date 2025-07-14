from openai import OpenAI
import os
from dotenv import load_dotenv


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


with open("prompts/intent_classifier.txt", "r", encoding="utf-8") as f:
    classifier_prompt = f.read()


def detect_booking_intent(user_input: str, last_bot_reply: str = "") -> bool:
    messages = [{"role": "system", "content": classifier_prompt},]

    if last_bot_reply:
        messages.append({"role": "assistant", "content": last_bot_reply})

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=messages,
        temperature=0.6,
        max_tokens=20,
    )
    intent = response.choices[0].message.content.strip().lower()

    if intent == "yes":
        return True

    return False
