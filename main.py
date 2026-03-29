import os
import json
import re
import llm
import stt
import tts
from audio import play_mp3_bytes
from actions._music import duck, unduck

# =========================
# Paths
# =========================
MODEL_PATH = "vosk-model-small-en-us-0.15"
SYSTEM_PROMPT_FILE = "system_prompt.txt"
MANIFEST_FILE = "actions/manifest.json"

# =========================
# Load system prompt & manifest ONCE
# =========================
with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
    MANIFEST = json.load(f)

# Pass manifest into llm module so it doesn't reload it
llm.set_manifest(MANIFEST)

# =========================
# Action module cache
# =========================
_action_module_cache: dict = {}

def handle_action(tool_json: dict) -> str:
    action_name = tool_json.get("action")
    args = tool_json.get("args", {})

    if action_name not in MANIFEST:
        return f"Action '{action_name}' is not allowed."

    expected_args = MANIFEST[action_name].get("args", {})
    for key, arg_info in expected_args.items():
        required = arg_info.get("required", True) if isinstance(arg_info, dict) else True
        if required and key not in args:
            return f"I'm missing some information to do that. Could you be more specific?"

    try:
        # Cache imported modules — avoids repeated __import__ overhead
        if action_name not in _action_module_cache:
            _action_module_cache[action_name] = __import__(
                f"actions.{action_name}", fromlist=["run"]
            )
        module = _action_module_cache[action_name]
        result = module.run(args)
        return result or "Action completed."
    except Exception as e:
        return f"Action error: {e}"

# =========================
# Output processing
# =========================
def process_output(output: dict) -> str:
    output_type = output.get("type")

    # LLM returned a validated command directly — no need to regex parse
    if output_type == "command":
        return handle_action(output["command"])

    # Plain chat response — strip <thinking> blocks (not spoken) and any embedded JSON
    message = output.get("message", "")
    speak_text = re.sub(r"<thinking>.*?</thinking>", "", message, flags=re.DOTALL)
    speak_text = re.sub(r"\{.*?\}", "", speak_text, flags=re.DOTALL).strip()
    return speak_text or "Done."

# =========================
# Main loop
# =========================
def main_loop():
    # Use a plain list; keep slot 0 for system prompt permanently
    chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    MAX_TURNS = 20  # pairs kept after system prompt

    while True:
        # transcript = stt.speech_to_text(MODEL_PATH)
        transcript = input("You: ")  # ← uncomment (and comment line above) to use text input instead of STT
        if not transcript:
            continue

        transcript = transcript.strip()
        if transcript.lower() in {"exit", "quit", "shutdown"}:
            break

        print(f"You: {transcript}")
        chat_history.append({"role": "user", "content": transcript})

        output = llm.large_language_model(chat_history)
        speak_text = process_output(output)

        print(f"iva: {speak_text}")

        # Store RAW assistant message (not tool result) for context continuity
        chat_history.append({"role": "assistant", "content": output.get("message", "")})

        # Trim in-place: keep system prompt + last MAX_TURNS messages
        if len(chat_history) > MAX_TURNS + 1:
            del chat_history[1 : len(chat_history) - MAX_TURNS]

        mp3_audio = tts.tts_gtts_bytes(speak_text)
        duck()
        play_mp3_bytes(mp3_audio)
        unduck()

# =========================
# Entry point
# =========================
if __name__ == "__main__":
    main_loop()