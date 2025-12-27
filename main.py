import os
import json
import re
import subprocess
import llm
import stt
import tts
from audio import play_mp3_bytes

# Paths
MODEL_PATH = os.path.join("vosk-model-small-en-us-0.15")
SYSTEM_PROMPT_FILE = "system_prompt.txt"

# Load system prompt from file
with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

# Chat history
chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]

def handle_action(tool_json):
    """Execute tool actions and return a speakable text"""
    action_name = tool_json.get("action")
    args = tool_json.get("args", {})

    if action_name == "open_file_explorer":
        path = args.get("path")
        if path:
            subprocess.Popen(f'explorer "{path}"')
            return f"Opening {os.path.basename(path)} folder."
        else:
            return "I don't know which folder to open."

    elif action_name == "run_command":
        from actions.terminal import run
        try:
            result = run(args)
            return result if result else "Command executed."
        except Exception as e:
            return f"Error running command: {e}"

    else:
        return f"Action {action_name} not implemented."

def get_user_input():
    """Replace with STT later; currently just input() for testing"""
    return input("You: ").strip()

def process_output(output):
    """Handle assistant output: separate JSON tool calls from speakable text"""
    message = output.get("message", "")

    # Extract JSON if present
    tool_json = None
    json_match = re.search(r"\{.*\}", message, re.DOTALL)
    if json_match:
        try:
            tool_json = json.loads(json_match.group())
        except json.JSONDecodeError:
            tool_json = None

    # Remove JSON from text
    speak_text = re.sub(r"\{.*\}", "", message, flags=re.DOTALL).strip()

    # If tool exists, handle it
    if tool_json:
        action_text = handle_action(tool_json)
        if action_text:
            speak_text = action_text

    # Fallback
    if not speak_text:
        speak_text = "Done."

    return speak_text

def main_loop():
    while True:
        transcript = stt.speech_to_text(MODEL_PATH)
        #transcript = get_user_input()
        if not transcript:
            continue

        print(f"You: {transcript}")
        chat_history.append({"role": "user", "content": transcript})

        output = llm.large_language_model(chat_history)
        speak_text = process_output(output)

        print(f"iva: {speak_text}")
        chat_history.append({"role": "assistant", "content": speak_text})

        # Speak
        mp3_audio = tts.tts_gtts_bytes(speak_text)
        play_mp3_bytes(mp3_audio)

        # Keep last 20 turns
        if len(chat_history) > 21:
            chat_history[:] = chat_history[:1] + chat_history[-20:]

if __name__ == "__main__":
    main_loop()
