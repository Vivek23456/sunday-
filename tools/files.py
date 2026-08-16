from pathlib import Path


SEARCH_ROOT = Path.home() / "Projects"

SKIP_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    "target",
    "dist",
    "build",
}


def find_files(query: str, max_results: int = 10) -> list[str]:
    query = query.lower().strip()

    if not query or not SEARCH_ROOT.exists():
        return []

    matches: list[tuple[int, str]] = []

    # Walk only directories/files under ~/Projects.
    for current_dir, dirnames, filenames in __import__("os").walk(
        SEARCH_ROOT
    ):
        current_path = Path(current_dir)

        # Don't descend into expensive/generated directories.
        dirnames[:] = [
            name
            for name in dirnames
            if name not in SKIP_DIRS
            and not name.startswith(".")
        ]

        # Check directory names.
        for dirname in dirnames:
            name = dirname.lower()

            if query in name:
                score = 0 if name == query else 1
                matches.append(
                    (
                        score,
                        str(current_path / dirname),
                    )
                )

        # Check filenames.
        for filename in filenames:
            name = filename.lower()

            if query in name:
                score = 0 if name == query else 2
                matches.append(
                    (
                        score,
                        str(current_path / filename),
                    )
                )

        if len(matches) >= max_results * 3:
            break

    matches.sort(key=lambda item: (item[0], item[1]))

    return [
        path
        for _, path in matches[:max_results]
    ]