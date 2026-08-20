from pathlib import Path

from tools.music.models import Track


MUSIC_ROOT = Path.home() / "Music" / "Sunday"

AUDIO_EXTENSIONS = {
    ".mp3",
    ".m4a",
    ".wav",
    ".flac",
    ".ogg",
    ".opus",
    ".aac",
}


def scan_library() -> list[Track]:
    if not MUSIC_ROOT.exists():
        return []

    tracks = []

    for path in MUSIC_ROOT.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in AUDIO_EXTENSIONS:
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


def search(query: str) -> list[Track]:
    query = query.strip().lower()

    if not query:
        return []

    tracks = scan_library()

    exact = []
    partial = []

    for track in tracks:
        title = track.title.lower()

        if title == query:
            exact.append(track)
        elif query in title:
            partial.append(track)

    return exact + partial

def playlist_names() -> list[str]:
    if not MUSIC_ROOT.exists():
        return []

    return sorted(
        path.name
        for path in MUSIC_ROOT.iterdir()
        if path.is_dir()
    )


def playlist_tracks(name: str) -> list[Track]:
    playlist_dir = MUSIC_ROOT / name

    if not playlist_dir.is_dir():
        return []

    tracks = []

    for path in playlist_dir.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in AUDIO_EXTENSIONS:
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