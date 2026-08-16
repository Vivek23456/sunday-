import subprocess
from pathlib import Path


PROJECTS_ROOT = Path.home() / "Projects"


def _normalize(value: str) -> str:
    return (
        value
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .strip()
    )


def discover_projects() -> list[dict]:
    if not PROJECTS_ROOT.exists():
        return []

    projects = []

    for path in PROJECTS_ROOT.iterdir():

        if not path.is_dir():
            continue

        if path.name.startswith("."):
            continue

        project = {
            "name": path.name,
            "path": str(path),
            "rust": (path / "Cargo.toml").exists(),
            "node": (path / "package.json").exists(),
            "python": (
                (path / "pyproject.toml").exists()
                or (path / "requirements.txt").exists()
            ),
            "git": (path / ".git").exists(),
        }

        languages = []

        if project["rust"]:
            languages.append("Rust")

        if project["node"]:
            languages.append("JavaScript/Node.js")

        if project["python"]:
            languages.append("Python")

        project["languages"] = languages

        projects.append(project)

    return projects


def find_project(query: str) -> dict | None:
    query = _normalize(query)

    if not query:
        return None

    projects = discover_projects()

    # Exact match
    for project in projects:

        name = _normalize(
            project["name"]
        )

        if name == query:
            return project

    # Partial match
    for project in projects:

        name = _normalize(
            project["name"]
        )

        if query in name:
            return project

    # Word-based match
    query_words = set(
        query.split()
    )

    best = None
    best_score = 0

    for project in projects:

        name_words = set(
            _normalize(
                project["name"]
            ).split()
        )

        score = len(
            query_words & name_words
        )

        if score > best_score:
            best_score = score
            best = project

    return best


def open_project(query: str) -> str:
    project = find_project(query)

    if project is None:
        return (
            f"I couldn't find a project "
            f"matching {query}."
        )

    try:

        subprocess.Popen(
            [
                "code",
                project["path"],
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return (
            f"Opening {project['name']}."
        )

    except Exception as exc:

        return (
            f"I found {project['name']}, "
            f"but couldn't open it: {exc}"
        )


def project_info(query: str) -> str:
    project = find_project(query)

    if project is None:
        return (
            f"I couldn't find a project "
            f"matching {query}."
        )

    if project["languages"]:
        language_text = ", ".join(
            project["languages"]
        )
    else:
        language_text = "Unknown"

    git_text = (
        "Git repository"
        if project["git"]
        else "Not a Git repository"
    )

    return (
        f"{project['name']} is located at "
        f"{project['path']}. "
        f"Languages: {language_text}. "
        f"{git_text}."
    )


def git_status(query: str) -> str:
    project = find_project(query)

    if project is None:
        return (
            f"I couldn't find a project "
            f"matching {query}."
        )

    if not project["git"]:
        return (
            f"{project['name']} is not "
            f"a Git repository."
        )

    try:

        result = subprocess.run(
            [
                "git",
                "status",
                "--short",
                "--branch",
            ],
            cwd=project["path"],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode != 0:
            return (
                f"Git status failed: "
                f"{result.stderr.strip()}"
            )

        output = result.stdout.strip()

        if not output:
            return (
                f"Git status for "
                f"{project['name']} is clean."
            )

        return (
            f"Git status for "
            f"{project['name']}:\n"
            f"{output}"
        )

    except subprocess.TimeoutExpired:
        return "Git status timed out."


def project_test(query: str) -> str:
    project = find_project(query)

    if project is None:
        return (
            f"I couldn't find a project "
            f"matching {query}."
        )

    if project["rust"]:
        command = [
            "cargo",
            "test",
        ]

    elif project["python"]:
        command = [
            "python",
            "-m",
            "pytest",
        ]

    elif project["node"]:
        command = [
            "npm",
            "test",
        ]

    else:
        return (
            f"I don't know how to test "
            f"{project['name']} yet."
        )

    try:

        result = subprocess.run(
            command,
            cwd=project["path"],
            capture_output=True,
            text=True,
            timeout=300,
        )

        output = (
            result.stdout.strip()
            or result.stderr.strip()
        )

        if result.returncode == 0:
            return (
                f"Tests passed for "
                f"{project['name']}.\n"
                f"{output[-3000:]}"
            )

        return (
            f"Tests failed for "
            f"{project['name']}.\n"
            f"{output[-3000:]}"
        )

    except subprocess.TimeoutExpired:
        return (
            f"Tests timed out for "
            f"{project['name']}."
        )


def project_build(query: str) -> str:
    project = find_project(query)

    if project is None:
        return (
            f"I couldn't find a project "
            f"matching {query}."
        )

    if project["rust"]:
        command = [
            "cargo",
            "build",
        ]

    elif project["node"]:
        command = [
            "npm",
            "run",
            "build",
        ]

    elif project["python"]:
        return (
            f"I found {project['name']}, "
            f"but there is no standard "
            f"Python build command configured."
        )

    else:
        return (
            f"I don't know how to build "
            f"{project['name']} yet."
        )

    try:

        result = subprocess.run(
            command,
            cwd=project["path"],
            capture_output=True,
            text=True,
            timeout=300,
        )

        output = (
            result.stdout.strip()
            or result.stderr.strip()
        )

        if result.returncode == 0:
            return (
                f"Build completed successfully "
                f"for {project['name']}.\n"
                f"{output[-3000:]}"
            )

        return (
            f"Build failed for "
            f"{project['name']}.\n"
            f"{output[-3000:]}"
        )

    except subprocess.TimeoutExpired:
        return (
            f"Build timed out for "
            f"{project['name']}."
        )