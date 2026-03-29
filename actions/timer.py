import threading
import time
from audio import play_mp3_bytes
from tts import tts_gtts_bytes

def run(args):
    """
    Sets a background timer.
    Expects args = { "seconds": int, "label": "string" }
    """
    # 1. Validate args - Use 'seconds' to match your prompt/manifest
    seconds = args.get("seconds")
    label = args.get("label", "Timer")

    if not isinstance(seconds, (int, float)) or seconds <= 0:
        return "I need a valid number of seconds to set a timer."

    # 2. The background task
    def background_timer(duration_sec, task_label):
        time.sleep(duration_sec)
        alert_text = f"Your {task_label} timer is up!"
        print(f"\n[TIMER] {alert_text}")
        
        try:
            # We call these here so it speaks even if you're in the middle of another chat
            audio_data = tts_gtts_bytes(alert_text)
            play_mp3_bytes(audio_data)
        except Exception as e:
            print(f"Timer alert error: {e}")

    # 3. Start thread - duration_sec is already 'seconds'
    timer_thread = threading.Thread(
        target=background_timer, 
        args=(seconds, label),
        daemon=True 
    )
    timer_thread.start()

    # 4. Return immediate confirmation
    # Logic check: if it's over 60, maybe describe it in minutes for the user's sake?
    if seconds >= 60:
        display_time = f"{seconds / 60:.1f} minutes"
    else:
        display_time = f"{seconds} seconds"

    return f"Alright, I've set a timer for {display_time} for {label}."