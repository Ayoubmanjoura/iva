"""
Shared music player for all music actions.
- Loads playlist metadata once at first play (no repeated yt-dlp calls)
- Playback runs in a background thread so IVA stays responsive
- Supports pause/resume via SIGSTOP/SIGCONT (Linux/Pi only)
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
ALSA_MIXER    = os.getenv("ALSA_MIXER", "Master")   # run `amixer scontrols` on Pi to find yours
DUCK_VOLUME   = int(os.getenv("DUCK_VOLUME", "25"))  # % while IVA is speaking
NORMAL_VOLUME = int(os.getenv("NORMAL_VOLUME", "85"))

# ── internal state ────────────────────────────────────────────────────────────
_tracks:   list[dict]              = []   # [{"title": str, "url": str}, ...]
_index:    int                     = 0
_proc:     subprocess.Popen | None = None
_paused:   bool                    = False
_lock:     threading.Lock          = threading.Lock()
_thread:   threading.Thread | None = None


# ── playlist loading ──────────────────────────────────────────────────────────
def _load_playlist() -> None:
    global _tracks
    if _tracks:
        return  # already loaded

    print("[music] Fetching playlist metadata...")
    ydl_opts = {
        "quiet":           True,
        "extract_flat":    True,   # only metadata, no download
        "skip_download":   True,
        "ignoreerrors":    True,
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
    """Set ALSA master volume to pct (0-100)."""
    try:
        subprocess.run(
            ["amixer", "sset", ALSA_MIXER, f"{pct}%"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        pass  # amixer not available (dev machine) — silently skip


def duck() -> None:
    """Lower volume so IVA can be heard over music."""
    set_volume(DUCK_VOLUME)


def unduck() -> None:
    """Restore normal volume after IVA finishes speaking."""
    set_volume(NORMAL_VOLUME)


# ── playback ──────────────────────────────────────────────────────────────────
def _stream(url: str) -> subprocess.Popen:
    """Start ffplay streaming audio-only from a YouTube URL."""
    stream_url = _get_stream_url(url)
    return subprocess.Popen(
        [
            "ffplay", "-nodisp", "-autoexit",
            "-loglevel", "quiet",
            "-vn",          # no video
            stream_url,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _get_stream_url(url: str) -> str:
    """Resolve a YouTube URL to a direct audio stream URL via yt-dlp."""
    ydl_opts = {
        "quiet":  True,
        "format": "bestaudio/best",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info["url"]


def _playback_loop(start_index: int) -> None:
    """Background thread: plays tracks sequentially from start_index."""
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

        proc.wait()  # block until song ends or process is killed

        with _lock:
            if _proc is None:
                # stop() was called — exit loop
                break

        i += 1

    with _lock:
        _proc = None
        _paused = False


def play(index: int = 0) -> None:
    global _thread
    stop()  # kill any current playback first
    _load_playlist()

    _thread = threading.Thread(target=_playback_loop, args=(index,), daemon=True)
    _thread.start()


def stop() -> None:
    global _proc, _paused
    with _lock:
        if _proc is not None:
            try:
                _proc.terminate()
            except ProcessLookupError:
                pass
            _proc = None
        _paused = False


def pause_resume() -> str:
    global _paused
    with _lock:
        if _proc is None:
            return "Nothing is playing."
        if not _paused:
            try:
                os.kill(_proc.pid, signal.SIGSTOP)
                _paused = True
                return "Music paused."
            except ProcessLookupError:
                return "Nothing is playing."
        else:
            try:
                os.kill(_proc.pid, signal.SIGCONT)
                _paused = False
                return "Music resumed."
            except ProcessLookupError:
                return "Nothing is playing."


def is_playing() -> bool:
    with _lock:
        return _proc is not None and not _paused


# ── helpers ───────────────────────────────────────────────────────────────────
def get_tracks() -> list[dict]:
    _load_playlist()
    return _tracks


def find_closest(query: str) -> int | None:
    """Fuzzy match query against track titles. Returns index or None."""
    if not _tracks:
        return None
    titles = [t["title"].lower() for t in _tracks]
    matches = difflib.get_close_matches(query.lower(), titles, n=1, cutoff=0.3)
    if matches:
        return titles.index(matches[0])
    # fallback: substring match
    for i, title in enumerate(titles):
        if query.lower() in title:
            return i
    return None