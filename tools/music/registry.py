from agent.registry import registry

from tools.music import (
    play_music,
    pause_music,
    resume_music,
    next_track,
    previous_track,
    stop_music,
    music_status,
    set_volume,
    random_music,
    play_playlist,
    play_random_playlist,
)


def register_music_tools():
    registry.register("music_play", play_music)
    registry.register("music_pause", pause_music)
    registry.register("music_resume", resume_music)
    registry.register("music_next", next_track)
    registry.register("music_previous", previous_track)
    registry.register("music_stop", stop_music)
    registry.register("music_status", music_status)
    registry.register("music_volume", set_volume)
    registry.register("music_random", random_music)
    registry.register("music_playlist", play_playlist)
    registry.register(
        "music_random_playlist",
        play_random_playlist,
    )