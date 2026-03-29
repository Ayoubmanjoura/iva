"""
Shared music player for all music actions.
- Loads playlist metadata once at first play (no repeated yt-dlp calls)
- Playback runs in a background thread so IVA stays responsive
- Supports pause/resume via SIGSTOP/SIGCONT on the whole process group
- Volume ducking via amixer for when IVA speaks
"""

import os
import signal
import subprocess
import threading
import difflib
import yt_dlp
from dotenv import load_dotenv

load_dotenv()

PLAYLIST_URL  = os.getenv("PLAYLIST_URL", "")
ALSA_MIXER    = os.getenv("ALSA_MIXER", "Master")
DUCK_VOLUME   = int(os.getenv("DUCK_VOLUME", "25"))
NORMAL_VOLUME = int(os.getenv("NORMAL_VOLUME", "85"))

# ── internal state ────────────────────────────────────────────────────────────
_tracks:   list[dict]              = []
_index:    int                     = 0
_proc:     subprocess.Popen | None = None
_paused:   bool                    = False
_lock:     threading.Lock          = threading.Lock()
_thread:   threading.Thread | None = None


# ── playlist loading ──────────────────────────────────────────────────────────
def _load_playlist() -> None:
    global _tracks
    if _tracks:
        return

    print("[music] Fetching playlist metadata...")
    ydl_opts = {
        "quiet":        True,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(PLAYLIST_URL, download=False)

    entries = info.get("entries", []) if info else []
    _tracks = [
        {"title": e["title"], "url": f"https://www.youtube.com/watch?v={e['id']}"}
        for e in entries
        if e and e.get("id") and e.get("title")
    ]
    print(f"[music] Loaded {len(_tracks)} tracks.")


# ── volume control ────────────────────────────────────────────────────────────
def set_volume(pct: int) -> None:
    try:
        subprocess.run(
            ["amixer", "sset", ALSA_MIXER, f"{pct}%"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        pass


def duck() -> None:
    set_volume(DUCK_VOLUME)


def unduck() -> None:
    set_volume(NORMAL_VOLUME)


# ── playback ──────────────────────────────────────────────────────────────────
def _get_stream_url(url: str) -> str:
    ydl_opts = {"quiet": True, "format": "bestaudio/best"}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info["url"]


def _stream(url: str) -> subprocess.Popen:
    """
    Launch ffplay in its own process group (start_new_session=True).
    This means SIGSTOP/SIGCONT via os.killpg hits ffplay AND all its
    child processes — so audio actually pauses.
    """
    stream_url = _get_stream_url(url)
    return subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-vn", stream_url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,  # own process group — key fix
    )


def _playback_loop(start_index: int) -> None:
    global _proc, _index, _paused

    i = start_index
    while i < len(_tracks):
        with _lock:
            _index = i
            _paused = False

        print(f"[music] Playing: {_tracks[i]['title']}")
        proc = _stream(_tracks[i]["url"])

        with _lock:
            _proc = proc

        proc.wait()

        with _lock:
            if _proc is None:
                break

        i += 1

    with _lock:
        _proc = None
        _paused = False


def play(index: int = 0) -> None:
    global _thread
    stop()
    _load_playlist()
    _thread = threading.Thread(target=_playback_loop, args=(index,), daemon=True)
    _thread.start()


def stop() -> None:
    global _proc, _paused
    with _lock:
        if _proc is not None:
            try:
                # Kill the whole process group
                os.killpg(os.getpgid(_proc.pid), signal.SIGTERM)
            except (ProcessLookupError, OSError):
                pass
            _proc = None
        _paused = False


def pause_resume() -> str:
    global _paused
    with _lock:
        if _proc is None:
            return "Nothing is playing."
        try:
            pgid = os.getpgid(_proc.pid)
        except OSError:
            return "Nothing is playing."

        if not _paused:
            try:
                os.killpg(pgid, signal.SIGSTOP)  # pause entire process group
                _paused = True
                return "Music paused."
            except OSError:
                return "Nothing is playing."
        else:
            try:
                os.killpg(pgid, signal.SIGCONT)  # resume entire process group
                _paused = False
                return "Music resumed."
            except OSError:
                return "Nothing is playing."


def is_playing() -> bool:
    with _lock:
        return _proc is not None and not _paused


# ── helpers ───────────────────────────────────────────────────────────────────
def get_tracks() -> list[dict]:
    _load_playlist()
    return _tracks


def find_closest(query: str) -> int | None:
    if not _tracks:
        return None
    titles = [t["title"].lower() for t in _tracks]
    matches = difflib.get_close_matches(query.lower(), titles, n=1, cutoff=0.3)
    if matches:
        return titles.index(matches[0])
    for i, title in enumerate(titles):
        if query.lower() in title:
            return i
    return None