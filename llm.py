import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")


def large_language_model(messages):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
        },
        json={
            "model": "xiaomi/mimo-v2-flash:free",
            "messages": messages,
            "max_tokens": 20,
            "temperature": 0.5,
        },
        timeout=30,
    )

    data = response.json()
    return data["choices"][0]["message"]["content"]
