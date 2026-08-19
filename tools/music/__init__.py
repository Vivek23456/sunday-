"""SUNDAY local music subsystem."""

from tools.music.player import (
    play_music,
    pause_music,
    resume_music,
    next_track,
    previous_track,
    stop_music,
    music_status,
    set_volume,
    random_music,
)

__all__ = [
    "play_music",
    "pause_music",
    "resume_music",
    "next_track",
    "previous_track",
    "stop_music",
    "music_status",
    "set_volume",
    "random_music",
]