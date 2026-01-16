# actions/stop_music.py
from audio_manager import manager


def run(args):
    manager.stop()
    return "Music stopped."
