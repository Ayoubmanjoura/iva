"""
actions/play_channel.py

Fetches the latest video from a named YouTube or Rumble channel
and streams its audio via ffplay using yt-dlp.

Requirements:
    pip install yt-dlp
    ffplay must be installed (already in the stack)

Add/edit channels in channels.json:
    {
        "friendly name": "https://www.youtube.com/@channel",
        "rumble channel": "https://rumble.com/c/channel"
    }
"""

import json
import subprocess
import os

CHANNELS_FILE = os.path.join(os.path.dirname(__file__), "..", "channels.json")

# yt-dlp flags shared across calls
_YTDLP_BASE = [
    "yt-dlp",
    "--no-playlist",          # only grab one video
    "--playlist-items", "1-10",  # check up to 10 latest — filter picks first match
    "--no-warnings",
    "--quiet",
    "--match-filter", "duration > 180",  # skip anything under 3 minutes (Shorts, Reels etc.)
]


def _load_channels() -> dict:
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        return {k.lower(): v for k, v in json.load(f).items()}


def _get_audio_url(channel_url: str) -> str | None:
    """Returns the best audio stream URL for the latest video on the channel."""
    result = subprocess.run(
        _YTDLP_BASE + [
            "--get-url",
            "--format", "bestaudio/best",
            channel_url,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    url = result.stdout.strip().splitlines()[0] if result.stdout.strip() else None
    return url


def _get_video_title(channel_url: str) -> str:
    """Returns the title of the latest video on the channel."""
    result = subprocess.run(
        _YTDLP_BASE + [
            "--get-title",
            channel_url,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip().splitlines()[0] if result.stdout.strip() else "Unknown title"


def run(args: dict) -> str:
    channel_name: str = args["channel"].lower().strip()

    channels = _load_channels()

    # Fuzzy match — allow partial names e.g. "lex" matches "lex fridman"
    matched_url = None
    for name, url in channels.items():
        if channel_name in name or name in channel_name:
            matched_url = url
            matched_name = name
            break

    if not matched_url:
        available = ", ".join(channels.keys())
        return f"I don't have a channel called '{channel_name}'. Available: {available}."

    try:
        title = _get_video_title(matched_url)
        audio_url = _get_audio_url(matched_url)
    except subprocess.TimeoutExpired:
        return "Timed out trying to fetch the channel."
    except FileNotFoundError:
        return "yt-dlp is not installed. Run: pip install yt-dlp"

    if not audio_url:
        return f"Could not find a playable video on {matched_name}."

    # Stream audio via ffplay (non-blocking — plays in background)
    subprocess.Popen(
        [
            "ffplay",
            "-nodisp",
            "-autoexit",
            "-loglevel", "quiet",
            audio_url,
        ]
    )

    return f"Playing: {title}"