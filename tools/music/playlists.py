import random
from pathlib import Path

from tools.music.library import MUSIC_ROOT
from tools.music.models import Track


def playlist_names() -> list[str]:
    if not MUSIC_ROOT.exists():
        return []

    return sorted(
        path.name
        for path in MUSIC_ROOT.iterdir()
        if path.is_dir()
    )


def load_playlist(name: str) -> list[Track]:
    playlist_dir = MUSIC_ROOT / name

    if not playlist_dir.is_dir():
        return []

    tracks = []

    for path in playlist_dir.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in {
            ".mp3",
            ".m4a",
            ".wav",
            ".flac",
            ".ogg",
            ".opus",
            ".aac",
        }:
            continue

        tracks.append(
            Track(
                title=path.stem,
                path=path,
            )
        )

    return sorted(
        tracks,
        key=lambda track: track.title.lower(),
    )


def shuffle_playlist(tracks: list[Track]) -> list[Track]:
    result = tracks.copy()
    random.shuffle(result)
    return result