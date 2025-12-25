import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

with open("actions/manifest.json") as f:
    ACTION_REGISTRY = json.load(f)


def large_language_model(messages):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
        },
        json={
            "model": "xiaomi/mimo-v2-flash:free",
            "messages": messages,
            "max_tokens": 512,
            "temperature": 0.5,
        },
        timeout=30,
    )
    print(response.json())
    data = response.json()
    content = data["choices"][0]["message"]["content"]

    try:
        cmd = json.loads(content)
        if is_valid_command(cmd, ACTION_REGISTRY):
            return {"type": "command", "command": cmd}
    except json.JSONDecodeError:
        pass

    return {"type": "chat", "message": content}


def is_valid_command(obj, registry):
    if not isinstance(obj, dict):
        return False
    if "action" not in obj or "args" not in obj:
        return False
    action = obj["action"]
    args = obj["args"]
    if action not in registry:
        return False
    expected_args = registry[action]["args"]
    if not isinstance(args, dict):
        return False
    for key, arg_type in expected_args.items():
        if key not in args:
            return False
        if arg_type == "string" and not isinstance(args[key], str):
            return False
    return True
