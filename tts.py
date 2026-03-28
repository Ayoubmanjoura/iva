import io
from gtts import gTTS


def tts_gtts_bytes(text: str, lang: str = "en") -> io.BytesIO:
    """
    Converts a plain text string to MP3 bytes via gTTS.
    main.py always passes a plain string after process_output().
    """
    mp3_fp = io.BytesIO()
    gTTS(text=str(text), lang=lang).write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp