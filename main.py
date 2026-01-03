import os
import json
import re
import subprocess
import llm
import stt
import tts
from audio import play_mp3_bytes

# =========================
# Paths
# =========================
MODEL_PATH = os.path.join("vosk-model-small-en-us-0.15")
SYSTEM_PROMPT_FILE = "system_prompt.txt"
MANIFEST_FILE = "actions/manifest.json"

# =========================
# Load system prompt
# =========================
with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

# =========================
# Load manifest
# =========================
with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
    MANIFEST = json.load(f)

# =========================
# Chat history
# =========================
chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]


# =========================
# Action dispatcher
# =========================
def handle_action(tool_json):
    action_name = tool_json.get("action")
    args = tool_json.get("args", {})

    # Validate action
    if action_name not in MANIFEST:
        return f"Action '{action_name}' is not allowed."

    # Validate args
    expected_args = MANIFEST[action_name].get("args", {})
    for key in expected_args:
        if key not in args:
            return f"Missing argument '{key}' for action '{action_name}'."

    try:
        # Dynamically import action module
        module = __import__(f"actions.{action_name}", fromlist=["run"])
        result = module.run(args)
        return result if result else "Action completed."

    except Exception as e:
        return f"Action error: {e}"


# =========================
# Input (STT placeholder)
# =========================
def get_user_input():
    return input("You: ").strip()


# =========================
# Output processing
# =========================
def process_output(output):
    message = output.get("message", "")

    tool_json = None

    # Try extracting JSON tool call
    json_match = re.search(r"\{.*\}", message, re.DOTALL)
    if json_match:
        try:
            tool_json = json.loads(json_match.group())
        except json.JSONDecodeError:
            tool_json = None

    # Remove JSON from spoken text
    speak_text = re.sub(r"\{.*\}", "", message, flags=re.DOTALL).strip()

    # Execute tool if present
    if tool_json:
        speak_text = handle_action(tool_json)

    if not speak_text:
        speak_text = "Done."

    return speak_text


# =========================
# Main loop
# =========================
def main_loop():
    while True:
        transcript = stt.speech_to_text(MODEL_PATH)
        # transcript = get_user_input()
        if not transcript:
            continue

        if transcript.lower() in {"exit", "quit", "shutdown"}:
            break

        print(f"You: {transcript}")
        chat_history.append({"role": "user", "content": transcript})

        output = llm.large_language_model(chat_history)

        speak_text = process_output(output)
        print(f"iva: {speak_text}")

        # IMPORTANT: store RAW assistant output, not tool result
        chat_history.append({"role": "assistant", "content": output.get("message", "")})

        # Speak
        mp3_audio = tts.tts_gtts_bytes(speak_text)
        play_mp3_bytes(mp3_audio)

        # Keep last 20 turns (+ system)
        if len(chat_history) > 21:
            chat_history[:] = chat_history[:1] + chat_history[-20:]


# =========================
# Entry point
# =========================
if __name__ == "__main__":
    main_loop()
