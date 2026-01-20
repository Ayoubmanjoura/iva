from pathlib import Path
import json
from mutagen import File

MUSIC_FOLDER = "/home/ayoub/music/sd"
INDEX_FILE = "music_index.json"
AUDIO_EXTS = (".mp3", ".wav", ".flac", ".m4a", ".ogg")


def _get_tag(tags, keys):
    if not tags:
        return None
    for key in keys:
        if key in tags:
            val = tags[key]
            return val[0] if isinstance(val, list) else str(val)
    return None


def run(args):
    files = list(Path(MUSIC_FOLDER).rglob("*"))
    audio_files = [f for f in files if f.suffix.lower() in AUDIO_EXTS]
    index = []

    for file in audio_files:
        try:
            audio = File(file)
            artist = _get_tag(audio.tags, ["TPE1", "artist", "ARTIST"])
            album = _get_tag(audio.tags, ["TALB", "album", "ALBUM"])
            track = _get_tag(audio.tags, ["TRCK", "tracknumber", "TRACKNUMBER"])
            track_num = int(str(track).split("/")[0]) if track else 0

            index.append(
                {
                    "path": str(file),
                    "artist": artist or "",
                    "album": album or "",
                    "track": track_num,
                }
            )
        except Exception:
            continue

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    return f"Indexed {len(index)} song(s) from {MUSIC_FOLDER}"
