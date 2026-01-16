import vlc
from audio import play_mp3_bytes
import time


class AudioManager:
    vlc_instance = vlc.Instance()
    player = vlc_instance.media_list_player_new()
    _inner_player = player.get_media_player()
    _playlists = {}  # store named playlists

    @classmethod
    def get_player(cls):
        return cls._inner_player

    # =========================
    # Playlist creation/management
    # =========================
    @classmethod
    def create_playlist(cls, name, song_paths):
        """Create a named playlist."""
        cls._playlists[name] = list(song_paths)

    @classmethod
    def add_to_playlist(cls, name, song_path):
        """Add a song to an existing playlist."""
        if name not in cls._playlists:
            cls._playlists[name] = []
        cls._playlists[name].append(song_path)

    @classmethod
    def remove_from_playlist(cls, name, song_path):
        """Remove a song from a playlist."""
        if name in cls._playlists and song_path in cls._playlists[name]:
            cls._playlists[name].remove(song_path)

    @classmethod
    def play_playlist(cls, name):
        """Play a named playlist."""
        if name not in cls._playlists:
            print(f"Playlist '{name}' does not exist.")
            return
        cls.player.stop()
        media_list = cls.vlc_instance.media_list_new()
        for path in cls._playlists[name]:
            media_list.add_media(cls.vlc_instance.media_new(str(path)))
        cls.player.set_media_list(media_list)
        cls.player.play()

    # =========================
    # Basic controls
    # =========================
    @classmethod
    def toggle_pause(cls):
        cls.player.pause()

    @classmethod
    def next_track(cls):
        cls.player.next()

    @classmethod
    def stop(cls):
        if cls.player:
            cls.player.stop()

    @classmethod
    def set_volume(cls, volume):
        if cls._inner_player:
            cls._inner_player.audio_set_volume(max(0, min(100, int(volume))))

    # =========================
    # Volume fading & TTS ducking
    # =========================
    @classmethod
    def fade_volume(cls, start, end, duration=0.5, steps=20):
        if not cls._inner_player:
            return
        step_delay = duration / steps
        delta = (end - start) / steps
        for i in range(steps):
            cls._inner_player.audio_set_volume(int(start + delta * i))
            time.sleep(step_delay)
        cls._inner_player.audio_set_volume(int(end))

    @classmethod
    def play_tts_with_duck(cls, tts_bytes, duck_level=30, fade_duration=0.5):
        player = cls.get_player()
        if player:
            original_volume = player.audio_get_volume()
            cls.fade_volume(
                original_volume, int(original_volume * duck_level / 100), fade_duration
            )

        play_mp3_bytes(tts_bytes)

        if player:
            cls.fade_volume(
                int(original_volume * duck_level / 100), original_volume, fade_duration
            )


# Singleton instance
manager = AudioManager()
