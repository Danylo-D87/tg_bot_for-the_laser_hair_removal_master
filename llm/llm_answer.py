from openai import OpenAI
import os
from dotenv import load_dotenv


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


with open("prompts/manager.txt", "r", encoding="utf-8") as f:
    system_prompt = f.read()


def get_llm_answer(user_input: str):

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        temperature=0.6,
        max_tokens=800
    )

    return response.choices[0].message.content.strip()
