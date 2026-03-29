# actions/play_radio.py
import subprocess
import requests
from actions._radio import get_process_registry

def _search_radio_browser(query: str) -> str | None:
    """Fallback: search Radio Browser API for a stream URL."""
    try:
        resp = requests.get(
            "https://de1.api.radio-browser.info/json/stations/search",
            params={
                "name": query,
                "limit": 1,
                "order": "votes",
                "reverse": "true",
                "hidebroken": "true",
            },
            timeout=5,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            return results[0]["url_resolved"]
    except requests.RequestException:
        pass
    return None


def run(args):
    """
    Plays a radio station by name.
    Expects args = { "station": "string" }
    """
    # 1. Validate args
    station = args.get("station", "").strip().lower()
    if not station:
        raise ValueError("Missing required argument: station")

    # 2. Favorites list — add your go-to stations here
    FAVORITES = {
        "rfi afrique":  "http://live02.rfi.fr/rfiafrique-64.mp3",
        "lofi hip hop": "https://streams.ilovemusic.de/iloveradio17.mp3",
        "kbcs":         "http://stream.pacificaservice.org:8000/kbcs",
        "berkley":      "https://stream.kalx.berkeley.edu:8443/kalx.flac",
        "oxford":       "https://web.smartradio.ro:8443/smartoxfordstreet",
        "kexp":         "https://kexp.streamguys1.com/kexp160.aac",
    }

    # 3. Resolve stream URL (favorites first, then API)
    stream_url = FAVORITES.get(station) or _search_radio_browser(station)
    if not stream_url:
        return f"Couldn't find a station matching '{station}'."

    # 4. Kill any currently playing station
    registry = get_process_registry()
    if registry.get("process") and registry["process"].poll() is None:
        registry["process"].terminate()

    # 5. Start playback in background (non-blocking so IVA stays responsive)
    proc = subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", stream_url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    registry["process"] = proc
    registry["station"] = station

    return f"Playing {station}."