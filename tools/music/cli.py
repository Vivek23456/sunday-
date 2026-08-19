import argparse

from tools.music.library import scan_library, search
from tools.music.player import (
    music_status,
    next_track,
    pause_music,
    play_music,
    previous_track,
    resume_music,
    set_volume,
    stop_music,
)


def main():
    parser = argparse.ArgumentParser(
        prog="sunday music",
        description="SUNDAY local music player",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    play = subparsers.add_parser("play")
    play.add_argument("query", nargs="+")

    subparsers.add_parser("pause")
    subparsers.add_parser("resume")
    subparsers.add_parser("next")
    subparsers.add_parser("previous")
    subparsers.add_parser("stop")
    subparsers.add_parser("status")

    volume = subparsers.add_parser("volume")
    volume.add_argument("value", type=int)

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")

    subparsers.add_parser("library")

    args = parser.parse_args()

    if args.command == "play":
        print(play_music(" ".join(args.query)))

    elif args.command == "pause":
        print(pause_music())

    elif args.command == "resume":
        print(resume_music())

    elif args.command == "next":
        print(next_track())

    elif args.command == "previous":
        print(previous_track())

    elif args.command == "stop":
        print(stop_music())

    elif args.command == "status":
        print(music_status())

    elif args.command == "volume":
        print(set_volume(args.value))

    elif args.command == "search":
        results = search(args.query)

        if not results:
            print("No matching songs.")

        for track in results:
            print(track.path)

    elif args.command == "library":
        tracks = scan_library()

        print(f"{len(tracks)} tracks")

        for track in tracks:
            print(track)


if __name__ == "__main__":
    main()

