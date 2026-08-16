import subprocess


def list_windows() -> list[str]:
    result = subprocess.run(
        ["wmctrl", "-l"],
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout.strip().splitlines()


def close_window(title: str) -> str:
    title = title.strip().lower()

    windows = list_windows()

    for line in windows:
        parts = line.split(None, 3)

        if len(parts) < 4:
            continue

        window_id = parts[0]
        window_title = parts[3]

        if title in window_title.lower():
            subprocess.run(
                ["wmctrl", "-i", "-c", window_id],
                check=True,
            )

            return f"Closed {window_title}."

    return f"I couldn't find a window matching {title}."


def close_all_windows() -> str:
    windows = list_windows()

    closed = 0

    for line in windows:
        parts = line.split(None, 3)

        if len(parts) < 4:
            continue

        window_id = parts[0]

        try:
            subprocess.run(
                ["wmctrl", "-i", "-c", window_id],
                check=True,
            )

            closed += 1

        except subprocess.CalledProcessError:
            pass

    return f"Closed {closed} windows."