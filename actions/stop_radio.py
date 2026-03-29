# actions/stop_radio.py
from actions._radio import get_process_registry

def run(args):
    """
    Stops the currently playing radio station.
    Expects args = {}
    """
    # 1. Check if anything is playing
    registry = get_process_registry()
    proc = registry.get("process")

    if not proc or proc.poll() is not None:
        return "No radio is currently playing."

    # 2. Stop it
    proc.terminate()
    station = registry.get("station", "the radio")
    registry["process"] = None
    registry["station"] = None

    return f"Stopped {station}."