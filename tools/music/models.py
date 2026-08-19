from dataclasses import dataclass
from pathlib import Path


@dataclass
class Track:
    title: str
    path: Path
    artist: str = ""
    album: str = ""
    genre: str = ""

    def __str__(self) -> str:
        if self.artist:
            return f"{self.title} — {self.artist}"
        return self.title


@dataclass
class PlayerState:
    current: Track | None = None
    status: str = "stopped"
    index: int = -1