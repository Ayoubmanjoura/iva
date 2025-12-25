from gtts import gTTS
import io


def tts_gtts_bytes(output, lang="en"):
    if isinstance(output, dict):
        # Only speak the human-readable part
        if output.get("type") == "chat":
            text = output.get("message", "")
        elif output.get("type") == "command":
            # Optional: announce the action being executed
            text = f"Executing {output['command']['action']}"
        else:
            text = ""
    else:
        text = str(output)  # fallback, just in case

    mp3_fp = io.BytesIO()
    tts = gTTS(text=text, lang=lang)
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp
