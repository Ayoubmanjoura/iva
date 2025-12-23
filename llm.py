import requests
import os
from dotenv import load_dotenv


def large_language_model(input):
    load_dotenv()

    API_KEY = os.getenv("OPENROUTER_API_KEY")

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
        },
        json={
            "model": "xiaomi/mimo-v2-flash:free",
            "messages": [{"role": "user", "content": input}],
        },
    )

    raw_output = response.json()
    output = raw_output["choices"][0]["message"]["content"]

    return output
