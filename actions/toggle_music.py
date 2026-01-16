from audio_manager import manager


def run(args):
    manager.toggle_pause()
    return "Toggled playback."
