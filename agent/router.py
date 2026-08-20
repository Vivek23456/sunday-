import json
import subprocess

import ollama
import psutil

from agent.permissions import requires_confirmation
from agent.registry import registry

from memory.store import memory as memory_store
from memory.projects import (
    open_project,
    project_info,
    git_status,
    project_test,
    project_build,
)

from tools.music.registry import register_music_tools

from tools.browser import open_url, search_web
from tools.files import find_files
from tools.playwright_browser import browser
from tools.windows import (
    close_window,
    close_all_windows,
)


MODEL = "llama3.2"


client = ollama.Client(
    host="http://127.0.0.1:11434",
    timeout=30,
)


register_music_tools()


SYSTEM_PROMPT = """
You are SUNDAY, a local laptop assistant.

Your ONLY job is to choose exactly one available tool.

Return ONLY valid JSON.
Do not explain.
Do not use markdown.
Do not write sentences outside JSON.

TOOLS:

open_application
{"name":"vscode|chrome|terminal"}

music_playlist
{"name":"playlist name"}

music_random_playlist
{"name":"playlist name"}

system_status
{}

find_files
{"query":"string"}

open_project
{"query":"project name"}

project_info
{"query":"project name"}

git_status
{"query":"project name"}

project_test
{"query":"project name"}

project_build
{"query":"project name"}

remember
{"key":"string","value":"string"}

recall
{"key":"string"}

forget
{"key":"string"}

open_url
{"url":"string"}

search_web
{"query":"string"}

browser_open
{"url":"string"}

browser_search
{"query":"string"}

browser_close
{}

close_window
{"title":"string"}

close_all_windows
{}

close_browser_tab
{}

close_all_browser_tabs
{}

run_shell
{"command":"string"}

music_play
{"query":"song name"}

music_pause
{}

music_resume
{}

music_next
{}

music_previous
{}

music_stop
{}

music_status
{}

music_volume
{"value":"integer"}

music_search
{"query":"song name"}

greet
{}

unknown
{}

EXAMPLES:
User: play something random
{"tool":"music_random","arguments":{}}

User: play my Gym playlist
{"tool":"music_playlist","arguments":{"name":"Gym"}}

User: play Hindi music
{"tool":"music_playlist","arguments":{"name":"Hindi"}}

User: play something random from Gym
{"tool":"music_random_playlist","arguments":{"name":"Gym"}}

User: play a random song from Hindi
{"tool":"music_random_playlist","arguments":{"name":"Hindi"}}

User: play a random song
{"tool":"music_random","arguments":{}}

User: surprise me
{"tool":"music_random","arguments":{}}

User: pick a random song
{"tool":"music_random","arguments":{}}

User: play anything
{"tool":"music_random","arguments":{}}

User: open vscode
{"tool":"open_application","arguments":{"name":"vscode"}}

User: open visual studio code
{"tool":"open_application","arguments":{"name":"vscode"}}

User: open my MEV engine
{"tool":"open_project","arguments":{"query":"MEV engine"}}

User: what language does my MEV project use
{"tool":"project_info","arguments":{"query":"MEV engine"}}

User: what is the git status of my MEV project
{"tool":"git_status","arguments":{"query":"MEV engine"}}

User: run the tests for my MEV project
{"tool":"project_test","arguments":{"query":"MEV engine"}}

User: build my MEV project
{"tool":"project_build","arguments":{"query":"MEV engine"}}

User: find my MEV project
{"tool":"find_files","arguments":{"query":"mev"}}

User: remember my MEV project is /home/vivek/Projects/mev-bot-infrastructure
{"tool":"remember","arguments":{"key":"mev_project","value":"/home/vivek/Projects/mev-bot-infrastructure"}}

User: where is my MEV project
{"tool":"recall","arguments":{"key":"mev_project"}}

User: forget my MEV project
{"tool":"forget","arguments":{"key":"mev_project"}}

User: open github
{"tool":"open_url","arguments":{"url":"https://github.com"}}

User: search for rust tokio
{"tool":"search_web","arguments":{"query":"rust tokio"}}

User: how is my computer doing
{"tool":"system_status","arguments":{}}

User: close vscode
{"tool":"close_window","arguments":{"title":"Visual Studio Code"}}

User: close all windows
{"tool":"close_all_windows","arguments":{}}

User: play Believer
{"tool":"music_play","arguments":{"query":"Believer"}}

User: play the song Believer
{"tool":"music_play","arguments":{"query":"Believer"}}

User: play believer by Imagine Dragons
{"tool":"music_play","arguments":{"query":"Believer"}}

User: pause the music
{"tool":"music_pause","arguments":{}}

User: resume the music
{"tool":"music_resume","arguments":{}}

User: next song
{"tool":"music_next","arguments":{}}

User: previous song
{"tool":"music_previous","arguments":{}}

User: stop the music
{"tool":"music_stop","arguments":{}}

User: what is playing
{"tool":"music_status","arguments":{}}

User: what song is playing
{"tool":"music_status","arguments":{}}

User: set volume to 50
{"tool":"music_volume","arguments":{"value":50}}

User: find Believer
{"tool":"music_search","arguments":{"query":"Believer"}}

User: hi
{"tool":"greet","arguments":{}}

"Go to sleep", "shut up", and "shutdown sunday" are handled by the application, not by you.
"""


def classify_command(text: str) -> dict:
    response = client.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        format="json",
        options={
            "temperature": 0,
        },
    )

    raw = response["message"]["content"].strip()

    print("Ollama:", raw)

    try:
        result = json.loads(raw)

        if not isinstance(result, dict):
            raise ValueError("Expected JSON object")

        tool = result.get("tool")

        if not isinstance(tool, str):
            raise ValueError("Missing tool")

        tool = tool.strip()

        if not tool:
            raise ValueError("Empty tool")

        arguments = result.get("arguments", {})

        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be an object")

        result["tool"] = tool
        result["arguments"] = arguments

        return result

    except Exception:
        print("Invalid tool decision.")
        print(raw)

        return {
            "tool": "unknown",
            "arguments": {},
        }

    
def execute_tool(
    tool: str,
    arguments: dict,
) -> str:

    # =====================================================
    # REGISTRY TOOLS
    # =====================================================

    if registry.has(tool):
        return registry.execute(
            tool,
            arguments,
        )

    # =====================================================
    # APPLICATIONS
    # =====================================================

    if tool == "open_application":

        name = (
            arguments
            .get("name", "")
            .strip()
            .lower()
        )

        commands = {
            "vscode": ["code"],
            "chrome": ["google-chrome"],
            "terminal": ["gnome-terminal"],
        }

        command = commands.get(name)

        if command is None:
            return (
                f"I don't know how to open {name}."
            )

        try:

            subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            return f"Opening {name}."

        except Exception as exc:

            return (
                f"I couldn't open {name}: {exc}"
            )

    # =====================================================
    # SYSTEM STATUS
    # =====================================================

    if tool == "system_status":

        cpu = psutil.cpu_percent(
            interval=0.5
        )

        memory_info = (
            psutil.virtual_memory()
        )

        return (
            f"CPU usage is {cpu:.0f} percent. "
            f"Memory usage is "
            f"{memory_info.percent:.0f} percent."
        )

    # =====================================================
    # FILE SEARCH
    # =====================================================

    if tool == "find_files":

        query = (
            arguments
            .get("query", "")
            .strip()
        )

        if not query:
            return (
                "Tell me what file or project "
                "to search for."
            )

        matches = find_files(query)

        if not matches:
            return (
                f"I couldn't find anything "
                f"matching {query}."
            )

        if len(matches) == 1:
            return (
                f"I found it at {matches[0]}."
            )

        formatted = "\n".join(
            f"- {path}"
            for path in matches[:5]
        )

        return (
            f"I found {len(matches)} matches:\n"
            f"{formatted}"
        )

    # =====================================================
    # PROJECTS
    # =====================================================

    if tool == "open_project":

        query = (
            arguments
            .get("query", "")
            .strip()
        )

        if not query:
            return (
                "Tell me which project "
                "to open."
            )

        return open_project(query)

    if tool == "project_info":

        query = (
            arguments
            .get("query", "")
            .strip()
        )

        if not query:
            return (
                "Tell me which project "
                "you want information about."
            )

        return project_info(query)

    if tool == "git_status":

        query = (
            arguments
            .get("query", "")
            .strip()
        )

        if not query:
            return (
                "Tell me which project "
                "you want Git status for."
            )

        return git_status(query)

    if tool == "project_test":

        query = (
            arguments
            .get("query", "")
            .strip()
        )

        if not query:
            return (
                "Tell me which project "
                "you want to test."
            )

        return project_test(query)

    if tool == "project_build":

        query = (
            arguments
            .get("query", "")
            .strip()
        )

        if not query:
            return (
                "Tell me which project "
                "you want to build."
            )

        return project_build(query)

    # =====================================================
    # MEMORY
    # =====================================================

    if tool == "remember":

        key = (
            arguments
            .get("key", "")
            .strip()
        )

        value = (
            arguments
            .get("value", "")
            .strip()
        )

        if not key or not value:
            return (
                "I need both a memory "
                "key and value."
            )

        memory_store.set(
            key,
            value,
        )

        return (
            f"I'll remember {key}."
        )

    if tool == "recall":

        key = (
            arguments
            .get("key", "")
            .strip()
        )

        if not key:
            return (
                "Tell me what you "
                "want me to remember."
            )

        value = memory_store.get(
            key
        )

        if value is None:
            return (
                f"I don't have anything "
                f"stored for {key}."
            )

        return (
            f"{key} is {value}."
        )

    if tool == "forget":

        key = (
            arguments
            .get("key", "")
            .strip()
        )

        if not key:
            return (
                "Tell me what you "
                "want me to forget."
            )

        deleted = memory_store.delete(
            key
        )

        if deleted:
            return (
                f"I forgot {key}."
            )

        return (
            f"I didn't have anything "
            f"stored for {key}."
        )

    # =====================================================
    # SIMPLE WEB
    # =====================================================

    if tool == "open_url":

        url = (
            arguments
            .get("url", "")
            .strip()
        )

        if not url:
            return (
                "Tell me which URL "
                "to open."
            )

        return open_url(url)

    if tool == "search_web":

        query = (
            arguments
            .get("query", "")
            .strip()
        )

        if not query:
            return (
                "Tell me what you "
                "want to search for."
            )

        return search_web(query)

    # =====================================================
    # PLAYWRIGHT BROWSER
    # =====================================================

    if tool == "browser_open":

        url = (
            arguments
            .get("url", "")
            .strip()
        )

        if not url:
            return (
                "Tell me which page "
                "to open."
            )

        return browser.open(url)

    if tool == "browser_search":

        query = (
            arguments
            .get("query", "")
            .strip()
        )

        if not query:
            return (
                "Tell me what you "
                "want to search for."
            )

        return browser.search_google(
            query
        )

    if tool == "browser_close":
        return browser.close()

    if tool == "close_browser_tab":
        return browser.close_current_tab()

    if tool == "close_all_browser_tabs":
        return browser.close_all_tabs()

    # =====================================================
    # WINDOWS
    # =====================================================

    if tool == "close_window":

        title = (
            arguments
            .get("title", "")
            .strip()
        )

        if not title:
            return (
                "Tell me which window "
                "to close."
            )

        return close_window(title)

    if tool == "close_all_windows":
        return close_all_windows()

    # =====================================================
    # SHELL
    # =====================================================

    if tool == "run_shell":

        command = (
            arguments
            .get("command", "")
            .strip()
        )

        if not command:
            return (
                "No shell command "
                "was provided."
            )

        try:

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

            output = (
                result.stdout.strip()
            )

            error = (
                result.stderr.strip()
            )

            if result.returncode != 0:
                return (
                    f"Command failed with "
                    f"exit code "
                    f"{result.returncode}.\n"
                    f"{error}"
                )

            return (
                output
                or "Command completed "
                "successfully."
            )

        except subprocess.TimeoutExpired:

            return (
                "The command timed out."
            )

    return "I didn't catch that."


def execute_command(
    text: str,
) -> str:

    print()

    print(
        f"Agent input: {text}"
    )

    decision = classify_command(
        text
    )

    print(
        "Tool decision:",
        json.dumps(
            decision,
            indent=2,
        ),
    )

    tool = decision.get(
        "tool",
        "unknown",
    )

    arguments = decision.get(
        "arguments",
        {},
    )

    if requires_confirmation(
        tool
    ):

        print()

        print(
            "⚠️ Confirmation required."
        )

        print(
            f"Tool: {tool}"
        )

        print(
            f"Arguments: {arguments}"
        )

        return (
            "__REQUIRES_CONFIRMATION__"
        )

    return execute_tool(
        tool,
        arguments,
    )