import llm
import stt
import tts
from audio import play_mp3_bytes
import os
from dotenv import load_dotenv
import subprocess

load_dotenv()

MODEL_PATH = os.path.join("vosk-model-small-en-us-0.15")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")

chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]

while True:
    transcript = stt.speech_to_text(MODEL_PATH)

    if not transcript.strip():
        continue

    print(f"User: {transcript}")
    chat_history.append({"role": "user", "content": transcript})

    output = llm.large_language_model(chat_history)

    # Handle commands
    if output.get("type") == "command":
        cmd = output["command"]["action"]
        args = output["command"].get("args", {})

        if cmd == "open_file_explorer":
            path = args.get("path")
            if path:
                subprocess.Popen(f'explorer "{path}"')
                speak_text = f"Opening {os.path.basename(path)} folder."
            else:
                speak_text = "I don't know which folder to open."
        else:
            speak_text = f"Command {cmd} received but not implemented."

    # Handle normal chat
    else:
        speak_text = output.get("message", "")

    print(f"iva: {speak_text}")
    chat_history.append({"role": "assistant", "content": speak_text})

    mp3_audio = tts.tts_gtts_bytes(speak_text)
    play_mp3_bytes(mp3_audio)

    # optional: keep last 10 turns
    if len(chat_history) > 21:
        chat_history = chat_history[:1] + chat_history[-20:]
