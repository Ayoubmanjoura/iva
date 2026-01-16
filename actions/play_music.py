# actions/play_music.py

from pathlib import Path
import platform
import vlc
from mutagen import File
import json
from audio_manager import manager

AUDIO_EXTS = (".mp3", ".wav", ".flac", ".m4a", ".ogg")
INDEX_FILE = "music_index.json"


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


def _load_index():
    if Path(INDEX_FILE).exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _filter_index(index, artist=None, album=None):
    filtered = []
    for item in index:
        if artist and artist.lower() not in item.get("artist", "").lower():
            continue
        if album and album.lower() not in item.get("album", "").lower():
            continue
        filtered.append(item)
    return filtered


def run(args):
    """
    Play audio files from the first detected USB drive.
    Optional args:
      - artist: str
      - album: str
    """
    if not isinstance(args, dict):
        raise ValueError("args must be a dictionary")

    artist = args.get("artist")
    album = args.get("album")

    # Security check
    forbidden = ["rm -rf", "format", "shutdown"]
    for val in (artist, album):
        if isinstance(val, str) and any(x in val.lower() for x in forbidden):
            raise PermissionError("Nice try.")

    # Try to load index first
    index = _load_index()
    song_list = []

    if index:
        filtered = _filter_index(index, artist=artist, album=album)
        song_list = sorted(filtered, key=lambda x: x.get("track", 0))
        song_list = [item["path"] for item in song_list]

    # Fallback: scan USB if no index or no matches
    if not song_list:
        usb_drives = _detect_usb_drives()
        if not usb_drives:
            return "No USB drives detected."
        usb = usb_drives[0]

        def _find_songs(root):
            for file in Path(root).rglob("*"):
                if file.suffix.lower() not in AUDIO_EXTS:
                    continue
                try:
                    audio = File(file)
                    if not audio or not audio.tags:
                        continue
                    a = _get_tag(audio.tags, ["TPE1", "artist", "ARTIST"])
                    al = _get_tag(audio.tags, ["TALB", "album", "ALBUM"])
                    if artist and (not a or artist.lower() not in a.lower()):
                        continue
                    if album and (not al or album.lower() not in al.lower()):
                        continue
                    yield file
                except Exception:
                    continue

        song_list = list(_find_songs(usb))
        if not song_list:
            return "No matching songs found."

        # Sort by track number
        def _track_number(file_path):
            try:
                audio = File(file_path)
                if not audio or not audio.tags:
                    return 0
                track = _get_tag(audio.tags, ["TRCK", "tracknumber", "TRACKNUMBER"])
                if track:
                    return int(str(track).split("/")[0])
            except Exception:
                pass
            return 0

        song_list.sort(key=_track_number)

    vlc_instance = vlc.Instance()
    player = vlc_instance.media_list_player_new()
    media_list = vlc_instance.media_list_new()
    for path in song_list:
        media_list.add_media(vlc_instance.media_new(str(path)))
    player.set_media_list(media_list)
    player.play()

    return f"Played {len(song_list)} song(s) from USB."
