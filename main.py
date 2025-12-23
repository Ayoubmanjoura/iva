import llm
import stt
import tts
from audio import play_mp3_bytes

MODEL_PATH = r"D:\Projects\iva\vosk-model-small-en-us-0.15"

transcript = stt.speech_to_text(MODEL_PATH)
print(f"User: {transcript}")

output = llm.large_language_model(transcript)
print(f"iva: {output}")

mp3_audio = tts.tts_gtts_bytes(output)
play_mp3_bytes(mp3_audio)
