from gtts import gTTS
import io


def tts_gtts_bytes(text, lang="en"):
    mp3_fp = io.BytesIO()
    tts = gTTS(text=text, lang=lang)
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp
