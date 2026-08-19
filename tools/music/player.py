import json
import os
import socket
import subprocess
import sys
import time

from tools.music.library import search
from tools.music.models import PlayerState, Track


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
        self._command(["stop"])

        return "Music stopped."

    def next(self) -> str:
        self._command(["playlist-next", "force"])

        return "Playing next track."

    def previous(self) -> str:
        self._command(["playlist-prev", "force"])

        return "Playing previous track."

    def volume(self, value: int) -> str:
        value = max(0, min(100, value))

        self._command(
            [
                "set_property",
                "volume",
                value,
            ]
        )

        return f"Volume set to {value}%."

    def status(self) -> str:
        if not self._socket_alive():
            return "Music player is not running."

        return "Music player is running."


player = MusicPlayer()


def play_music(query: str) -> str:
    return player.play(query)


def pause_music() -> str:
    return player.pause()


def resume_music() -> str:
    return player.resume()


def next_track() -> str:
    return player.next()


def previous_track() -> str:
    return player.previous()


def stop_music() -> str:
    return player.stop()


def music_status() -> str:
    return player.status()


def set_volume(value: int) -> str:
    return player.volume(value)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: "
            "python3 -m tools.music.player <song>"
        )
        raise SystemExit(1)

    query = " ".join(sys.argv[1:])

    print(play_music(query))