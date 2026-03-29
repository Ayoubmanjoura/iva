import threading
import time
from audio import play_mp3_bytes
from tts import tts_gtts_bytes
from actions._music import duck, unduck


def run(args):
    seconds = args.get("seconds")
    label = args.get("label", "Timer")

    if not isinstance(seconds, (int, float)) or seconds <= 0:
        return "I need a valid number of seconds to set a timer."

    def background_timer(duration_sec, task_label):
        time.sleep(duration_sec)
        alert_text = f"Your {task_label} timer is up!"
        print(f"\n[TIMER] {alert_text}")
        try:
            duck()
            audio_data = tts_gtts_bytes(alert_text)
            play_mp3_bytes(audio_data)
            unduck()
        except Exception as e:
            print(f"Timer alert error: {e}")

    threading.Thread(
        target=background_timer,
        args=(seconds, label),
        daemon=True
    ).start()

    if seconds >= 60:
        display_time = f"{seconds / 60:.1f} minutes"
    else:
        display_time = f"{int(seconds)} seconds"

    return f"Alright, I've set a timer for {display_time} for {label}."