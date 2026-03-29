# actions/_radio.py
"""
Shared state for radio playback.
Holds the ffplay process and current station name so
play_radio and stop_radio can both access it.
"""

_registry: dict = {
    "process": None,
    "station": None,
}

def get_process_registry() -> dict:
    return _registry