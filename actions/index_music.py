# actions/index_music.py

from pathlib import Path
from mutagen import File
import platform
import json

INDEX_FILE = "music_index.json"
AUDIO_EXTS = (".mp3", ".wav", ".flac", ".m4a", ".ogg")


def _get_tag(tags, key_list):
    if not tags:
        return None
    for key in key_list:
        if key in tags:
            val = tags[key]
            return val[0] if isinstance(val, list) else str(val)
    return None


def _detect_usb_drives():
    system = platform.system()
    if system == "Windows":
        try:
            import win32api, win32file

            drives = win32api.GetLogicalDriveStrings().split("\000")[:-1]
            return [
                d
                for d in drives
                if win32file.GetDriveType(d) == win32file.DRIVE_REMOVABLE
            ]
        except ImportError:
            return []
    media = Path("/media")
    if not media.exists():
        return []
    return [str(d) for d in media.iterdir() if d.is_dir()]


def run(args):
    """
    Index all audio files on the first detected USB drive.
    Expects args = { } (no required parameters)
    Shows percentage progress while indexing.
    """

    # 1. Validate args
    if not isinstance(args, dict):
        raise ValueError("args must be a dictionary")

    # 2. Security checks
    forbidden_keywords = ["rm -rf", "format", "shutdown"]
    for val in args.values():
        if isinstance(val, str) and any(x in val.lower() for x in forbidden_keywords):
            raise PermissionError("This operation is not allowed")

    # 3. Detect USB
    usb_drives = _detect_usb_drives()
    if not usb_drives:
        return "No USB drives detected."
    usb = usb_drives[0]

    # 4. Collect audio files
    files = list(Path(usb).rglob("*"))
    audio_files = [f for f in files if f.suffix.lower() in AUDIO_EXTS]
    total_files = len(audio_files)
    index = []

    if total_files == 0:
        return "No audio files found on USB."

    # 5. Indexing with percentage progress
    for i, file in enumerate(audio_files, start=1):
        try:
            audio = File(file)
            if not audio or not audio.tags:
                continue
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

        # Print percentage every 2%
        percent = int((i / total_files) * 100)
        if percent % 2 == 0 and i != total_files:
            print(f"Indexing: {percent}% done...", end="\r")

    # 6. Save index
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    # 7. Done message
    print(f"Indexing: 100% done!                      ")
    return f"Indexed {len(index)} song(s) from USB."
