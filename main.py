import threading
import re
import json
import os
import llm
import stt
import tts
from audio import play_mp3_bytes
import audio_manager
from automations.alarm import start_scheduler

# =========================
# Paths & files
# =========================
MODEL_PATH = "vosk-model-en-us-0.22"
SYSTEM_PROMPT_FILE = "system_prompt.txt"
MANIFEST_FILE = "actions/manifest.json"

with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
    MANIFEST = json.load(f)

chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]
manager = audio_manager.AudioManager()


# =========================
# Action executor (fixed)
# =========================
def handle_action(tool_json):
    action_name = tool_json.get("action")
    args = tool_json.get("args", {})

    if action_name not in MANIFEST:
        return f"Action '{action_name}' is not allowed."

    expected_args = MANIFEST[action_name].get("args", {})
    for key, meta in expected_args.items():
        # FIXED: check for key existence instead of truthiness
        if meta.get("required", True) and key not in args:
            return f"Missing argument '{key}' for action '{action_name}'."

    try:
        module = __import__(f"actions.{action_name}", fromlist=["run"])
        return module.run(args) or "Action completed."
    except Exception as e:
        return f"Action error: {e}"


# =========================
# Input
# =========================
def get_user_input():
    # Replace with STT if needed
    try:
        return stt.speech_to_text(MODEL_PATH) or ""
    except Exception as e:
        print(f"STT error: {e}")
        return input("You: ").strip()


# =========================
# Output processing (fixed)
# =========================
def process_output(output):
    message = output.get("message", "")

    tool_json = None

    # if LLM explicitly says type=command, just use command
    if output.get("type") == "command":
        tool_json = output.get("command")
    else:
        # TRY full JSON first
        try:
            tool_json = json.loads(message)
        except json.JSONDecodeError:
            # fallback: extract JSON from text
            match = re.search(r"\{.*\}", message, re.DOTALL)
            if match:
                try:
                    tool_json = json.loads(match.group())
                except json.JSONDecodeError:
                    tool_json = None

    # Remove JSON from message for clean speech output
    speak_text = re.sub(r"\{.*\}", "", message, flags=re.DOTALL).strip()

    if tool_json:
        speak_text = handle_action(tool_json) or speak_text

    return speak_text or "Done."


# =========================
# Main Loop
# =========================
def main_loop():
    try:
        while True:
            transcript = get_user_input()
            # transcript = input("You: ").strip()
            if not transcript:
                continue

            if transcript.lower() in {"exit", "quit", "shutdown"}:
                print("Shutting down...")
                break

            print(f"You: {transcript}")
            chat_history.append({"role": "user", "content": transcript})

            output = llm.large_language_model(chat_history) or {"message": ""}
            speak_text = process_output(output)
            print(f"iva: {speak_text}")

            chat_history.append(
                {"role": "assistant", "content": output.get("message", "")}
            )

            # TTS with ducking
            try:
                mp3_audio = tts.tts_gtts_bytes(speak_text)
                manager.play_tts_with_duck(mp3_audio)
            except Exception as e:
                print(f"TTS error: {e}")

            # Keep last 20 turns + system
            if len(chat_history) > 21:
                chat_history[:] = chat_history[:1] + chat_history[-20:]

    except KeyboardInterrupt:
        print("\nLoop stopped by user.")


# =========================
# Entry point
# =========================
if __name__ == "__main__":
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    main_loop()
