import requests
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

# Manifest injected by main.py — avoids loading the file a second time
_ACTION_REGISTRY: dict = {}

def set_manifest(manifest: dict) -> None:
    """Called once by main.py to share the already-loaded manifest."""
    global _ACTION_REGISTRY
    _ACTION_REGISTRY = manifest

# =========================
# Command validation
# =========================

# Maps manifest type strings to Python type checks.
# Split on space to strip range hints like "int (0-255)" → "int"
_TYPE_VALIDATORS = {
    "string":  lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "int":     lambda v: isinstance(v, int) and not isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
}

def _is_valid_command(obj: dict) -> bool:
    if not isinstance(obj, dict):
        return False
    if "action" not in obj:
        return False

    # Default missing args to {} — model sometimes omits it for arg-less actions
    if "args" not in obj:
        obj["args"] = {}

    action = obj["action"]
    args = obj["args"]

    if action not in _ACTION_REGISTRY:
        return False
    if not isinstance(args, dict):
        return False

    for key, arg_info in _ACTION_REGISTRY[action]["args"].items():
        # arg_info is {"type": "boolean", "required": true} — extract the type string
        arg_type = arg_info.get("type", "string") if isinstance(arg_info, dict) else str(arg_info)
        base_type = arg_type.split()[0].lower()  # strip range hints e.g. "int (0-255)" → "int"

        required = arg_info.get("required", True) if isinstance(arg_info, dict) else True
        if key not in args:
            if required:
                return False
            continue  # optional arg, skip type check

        validator = _TYPE_VALIDATORS.get(base_type)
        if validator and not validator(args[key]):
            return False

    return True

# =========================
# LLM call
# =========================
def large_language_model(messages: list) -> dict:
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
                "messages": messages,
                "max_tokens": 512,
                "temperature": 0.5,
            },
            timeout=30,
        )
        response.raise_for_status()          # raises on 4xx / 5xx
        data = response.json()               # single parse
    except requests.exceptions.Timeout:
        return {"type": "chat", "message": "Sorry, the request timed out."}
    except requests.exceptions.RequestException as e:
        return {"type": "chat", "message": f"Network error: {e}"}
    except (KeyError, IndexError, ValueError):
        return {"type": "chat", "message": "Unexpected response from the model."}

    content: str = data["choices"][0]["message"]["content"]

    # Extract JSON even if the model wrapped it in text e.g. "Sure! {"action": ...}"
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        try:
            cmd = json.loads(json_match.group())
            if _is_valid_command(cmd):
                return {"type": "command", "command": cmd}
        except (json.JSONDecodeError, TypeError):
            pass

    return {"type": "chat", "message": content}