import requests
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

_ACTION_REGISTRY: dict = {}

def set_manifest(manifest: dict) -> None:
    global _ACTION_REGISTRY
    _ACTION_REGISTRY = manifest

_TYPE_VALIDATORS = {
    "string":  lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "int":     lambda v: isinstance(v, int) and not isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
}

def _is_valid_command(obj: dict) -> bool:
    if not isinstance(obj, dict):
        print("DEBUG: Command is not a dictionary.")
        return False
    if "action" not in obj:
        print("DEBUG: 'action' key missing in JSON.")
        return False

    if "args" not in obj:
        obj["args"] = {}

    action = obj["action"]
    args = obj["args"]

    if action not in _ACTION_REGISTRY:
        print(f"DEBUG: Action '{action}' not found in manifest.")
        return False
    
    for key, arg_info in _ACTION_REGISTRY[action]["args"].items():
        arg_type = arg_info.get("type", "string") if isinstance(arg_info, dict) else str(arg_info)
        base_type = arg_type.split()[0].lower() 
        required = arg_info.get("required", True) if isinstance(arg_info, dict) else True
        
        if key not in args:
            if required:
                print(f"DEBUG: Missing required arg '{key}' for action '{action}'.")
                return False
            continue 

        validator = _TYPE_VALIDATORS.get(base_type)
        if validator and not validator(args[key]):
            print(f"DEBUG: Type mismatch for '{key}'. Expected {base_type}, got {type(args[key])}.")
            return False

    return True

def large_language_model(messages: list) -> dict:
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "nvidia/nemotron-3-super-120b-a12b:free",
                "messages": messages,
                "max_tokens": 512,
                "temperature": 0.5,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return {"type": "chat", "message": f"LLM Error: {e}"}

    content: str = data["choices"][0]["message"]["content"]
    
    # === DEBUG PRINT ===
    print(f"\n--- RAW LLM OUTPUT ---\n{content}\n----------------------\n")

    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        try:
            raw_json = json_match.group()
            cmd = json.loads(raw_json)
            if _is_valid_command(cmd):
                return {"type": "command", "command": cmd}
            else:
                print("DEBUG: JSON found but failed validation.")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"DEBUG: JSON Decode Error: {e}")

    return {"type": "chat", "message": content}