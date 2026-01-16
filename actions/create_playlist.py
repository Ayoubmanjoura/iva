# actions/create_playlist.py

import json
import requests
import os
import re
from dotenv import load_dotenv


def run(args):
    """
    Creates a playlist from a local music index using OpenRouter.
    Expects args = {
        "theme": "string",
        "music_index_path": "string (optional)"
    }
    """

    # =========================
    # 1. Validate args
    # =========================
    theme = args.get("theme")
    if not theme:
        raise ValueError("Missing required argument: theme")

    music_index_path = args.get("music_index_path", "music_index.json")

    if not os.path.exists(music_index_path):
        raise FileNotFoundError(f"Music index not found: {music_index_path}")

    # =========================
    # 2. Security / sanity checks
    # =========================
    forbidden = ["rm -rf", "delete system", "nuke"]
    if any(x.lower() in theme.lower() for x in forbidden):
        raise PermissionError("Theme contains forbidden content")

    # =========================
    # 3. Setup OpenRouter
    # =========================
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not found in .env")

    with open(music_index_path, "r", encoding="utf-8") as f:
        music_index = json.load(f)

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "xiaomi/mimo-v2-flash:free",
        "messages": [
            {
                "role": "user",
                "content": (
                    "Using the following music index, create a playlist of 10 songs.\n"
                    "Output ONLY a JSON array of objects.\n"
                    "Each object must contain:\n"
                    '- "title" (with extension)\n'
                    '- "directory"\n\n'
                    f"Music Index:\n{json.dumps(music_index)}\n\n"
                    f"Theme: {theme}"
                ),
            }
        ],
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    response_json = response.json()

    raw_content = response_json["choices"][0]["message"]["content"]

    # =========================
    # 4. Clean & parse JSON
    # =========================
    def extract_json_array(text: str) -> str:
        text = re.sub(r"```json|```", "", text).strip()

        start = text.find("[")
        end = text.rfind("]") + 1

        if start == -1 or end == 0:
            raise ValueError("Model did not return a JSON array")

        return text[start:end]

    clean_json = extract_json_array(raw_content)
    playlist = json.loads(clean_json)

    # =========================
    # 5. Save playlist
    # =========================
    with open("playlist.json", "w", encoding="utf-8") as f:
        json.dump(playlist, f, indent=4, ensure_ascii=False)

    # =========================
    # 6. Return plain text
    # =========================
    titles = [song.get("title", "UNKNOWN TITLE") for song in playlist]

    output = "Playlist Created:\n"
    for i, title in enumerate(titles, start=1):
        output += f"{i}. {title}\n"

    return output
