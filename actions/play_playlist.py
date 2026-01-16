# actions/play_playlist.py

import json
import os
import threading
from pathlib import Path
from audio_manager import manager

PLAYLIST_FILE = "playlist.json"


def _load_playlist():
    if not Path(PLAYLIST_FILE).exists():
        raise FileNotFoundError(f"Playlist not found: {PLAYLIST_FILE}")
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        playlist = json.load(f)
    if not playlist:
        raise RuntimeError("Playlist is empty")
    return playlist


def _build_song_list(playlist):
    song_list = []
    for song in playlist:
        title = song.get("title")
        directory = song.get("directory")
        if not title or not directory:
            continue
        path = os.path.join(directory, title)
        if os.path.exists(path):
            song_list.append(path)
    return song_list


def _play_async(song_list):
    # Create a temporary playlist in AudioManager and play it
    playlist_name = "_temp_playlist"
    manager.create_playlist(playlist_name, song_list)
    manager.play_playlist(playlist_name)


def run(args):
    """
    Plays songs from playlist.json asynchronously.
    Returns immediately so main.py can keep running.
    """
    playlist = _load_playlist()
    song_list = _build_song_list(playlist)

    if not song_list:
        return "No valid songs found in playlist."

    # Spawn a thread to play the playlist
    t = threading.Thread(target=_play_async, args=(song_list,), daemon=True)
    t.start()

    # Print playlist info instantly
    titles = [Path(s).name for s in song_list]
    playlist_str = "\n".join(f" {i + 1}. {title}" for i, title in enumerate(titles))
    print("🎶 Playing playlist:\n" + playlist_str)

    return f"Started playing {len(song_list)} song(s) 🎧"
