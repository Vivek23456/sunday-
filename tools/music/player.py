import json
import os
import random
import socket
import subprocess
import sys
import time

from tools.music.models import PlayerState, Track
from tools.music.library import (
    scan_library,
    search,
    playlist_tracks,
)

IPC_SOCKET = "/tmp/sunday-mpv.sock"


class MusicPlayer:
    def __init__(self):
        self.queue: list[Track] = []
        self.index = -1
        self.state = PlayerState()

    def _socket_alive(self) -> bool:
        if not os.path.exists(IPC_SOCKET):
            return False

        try:
            with socket.socket(
                socket.AF_UNIX,
                socket.SOCK_STREAM,
            ) as sock:
                sock.settimeout(0.5)
                sock.connect(IPC_SOCKET)

            return True

        except (OSError, ConnectionRefusedError):
            return False

    def _start_mpv(self):
        if self._socket_alive():
            return

        if os.path.exists(IPC_SOCKET):
            os.remove(IPC_SOCKET)

        subprocess.Popen(
            [
                "mpv",
                "--no-video",
                "--idle=yes",
                "--force-window=no",
                f"--input-ipc-server={IPC_SOCKET}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        for _ in range(50):
            if self._socket_alive():
                return

            time.sleep(0.1)

        raise RuntimeError(
            "Could not connect to mpv."
        )

    def _command(self, command: list):
        self._start_mpv()

        payload = {
            "command": command,
        }

        with socket.socket(
            socket.AF_UNIX,
            socket.SOCK_STREAM,
        ) as sock:
            sock.connect(IPC_SOCKET)
            sock.sendall(
                (json.dumps(payload) + "\n").encode()
            )



    def play(self, query: str) -> str:
        matches = search(query)

        if not matches:
            return (
                f"I couldn't find '{query}' "
                "in your music library."
            )

        self.queue = matches
        self.index = 0

        track = self.queue[self.index]

        self._command(
            [
                "loadfile",
                str(track.path),
                "replace",
            ]
        )

        self.state = PlayerState(
            current=track,
            status="playing",
            index=self.index,
        )

        return f"Playing {track}."

    def random(self) -> str:
        tracks = scan_library()

        if not tracks:
            return "Your music library is empty."

        track = random.choice(tracks)

        self.queue = [track]
        self.index = 0

        self._command(
            [
                "loadfile",
                str(track.path),
                "replace",
            ]
        )

        self.state = PlayerState(
            current=track,
            status="playing",
            index=0,
        )

        return f"Playing random track: {track}."

    def pause(self) -> str:
        self._command(
            [
                "set_property",
                "pause",
                True,
            ]
        )

        return "Music paused."

    def resume(self) -> str:
        self._command(
            [
                "set_property",
                "pause",
                False,
            ]
        )

        return "Music resumed."

    def stop(self) -> str:
        self._command(
            ["stop"]
        )

        return "Music stopped."

    def next(self) -> str:
        self._command(
            [
                "playlist-next",
                "force",
            ]
        )

        return "Playing next track."

    def previous(self) -> str:
        self._command(
            [
                "playlist-prev",
                "force",
            ]
        )

        return "Playing previous track."

    def volume(self, value: int) -> str:
        value = max(
            0,
            min(100, value),
        )

        self._command(
            [
                "set_property",
                "volume",
                value,
            ]
        )

        return f"Volume set to {value}%."
    

    def play_playlist(self, name: str) -> str:
        tracks = playlist_tracks(name)

        if not tracks:
            return (
                f"I couldn't find the playlist "
                f"'{name}'."
            )

        self.queue = tracks
        self.index = 0

        track = self.queue[self.index]

        self._command(
            [
                "loadfile",
                str(track.path),
                "replace",
            ]
        )

        self.state = PlayerState(
            current=track,
            status="playing",
            index=0,
        )

        return (
            f"Playing {name} playlist "
            f"with {len(tracks)} tracks."
        )

    def play_random_playlist(self, name: str) -> str:
        tracks = playlist_tracks(name)

        if not tracks:
            return (
                f"I couldn't find the playlist "
                f"'{name}'."
            )

        random.shuffle(tracks)

        self.queue = tracks
        self.index = 0

        track = self.queue[self.index]

        self._command(
            [
                "loadfile",
                str(track.path),
                "replace",
            ]
        )

        self.state = PlayerState(
            current=track,
            status="playing",
            index=0,
        )

        return (
            f"Playing a random track "
            f"from {name}: {track}."
        )
    
    def status(self) -> str:
        if not self._socket_alive():
            return "Music player is not running."

        return "Music player is running."


player = MusicPlayer()


def play_music(
    query: str,
) -> str:
    return player.play(query)


def random_music() -> str:
    return player.random()


def pause_music() -> str:
    return player.pause()


def resume_music() -> str:
    return player.resume()


def next_track() -> str:
    return player.next()


def previous_track() -> str:
    return player.previous()

def play_playlist(name: str) -> str:
    return player.play_playlist(name)


def stop_music() -> str:
    return player.stop()


def music_status() -> str:
    return player.status()

def play_playlist(name: str) -> str:
    return player.play_playlist(name)


def play_random_playlist(name: str) -> str:
    return player.play_random_playlist(name)


def set_volume(
    value: int,
) -> str:
    return player.volume(value)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(
            "Usage: "
            "python3 -m tools.music.player <song>"
        )

        raise SystemExit(1)

    query = " ".join(
        sys.argv[1:]
    )

    print(
        play_music(query)
    )