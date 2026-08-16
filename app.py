import time

from audio.clap import wait_for_clap
from audio.record import record_command
from audio.transcribe import transcribe
from audio.tts import speak

from agent.permissions import requires_confirmation
from agent.router import classify_command, execute_tool


COMMAND_FILE = "command.wav"


SLEEP_COMMANDS = {
    "shut up",
    "shut",
    "stop listening",
    "go to sleep",
    "sleep",
    "be quiet",
    "quiet",
}

EXIT_COMMANDS = {
    "shutdown sunday",
    "exit sunday",
    "quit sunday",
}


def valid_transcription(text: str) -> bool:
    if not text:
        return False

    words = text.lower().split()

    if len(words) == 0:
        return False

    # Reject obvious repetition/hallucination.
    if len(words) >= 4:
        unique_words = set(words)

        if len(unique_words) <= 2:
            return False

    return True


def get_voice_command() -> str | None:
    audio_file = record_command(COMMAND_FILE)

    if not audio_file:
        return None

    print("\nTranscribing...")

    text = transcribe(audio_file).strip()

    if not valid_transcription(text):
        print("Ignoring unreliable transcription.")
        return None

    print(f"You: {text}")

    return text

def is_sleep_command(text: str) -> bool:
    normalized = (
        text.lower()
        .strip()
        .strip(".,!?")
    )

    phrases = (
        "shut up",
        "stop listening",
        "go to sleep",
        "go quiet",
        "be quiet",
        "sleep",
        "quiet",
    )

    return any(
        phrase in normalized
        for phrase in phrases
    )

def is_exit_command(text: str) -> bool:
    normalized = (
        text.lower()
        .strip()
        .strip(".,!?")
    )

    phrases = (
        "shutdown sunday",
        "shut down sunday",
        "exit sunday",
        "quit sunday",
    )

    return any(
        phrase in normalized
        for phrase in phrases
    )

def confirmation_response() -> bool:
    speak(
        "This action requires confirmation. "
        "Should I proceed?"
    )

    response = get_voice_command()

    if not response:
        return False

    text = response.lower().strip()

    positive = {
        "yes",
        "yeah",
        "yep",
        "sure",
        "okay",
        "ok",
        "go ahead",
        "proceed",
        "do it",
        "confirm",
    }

    negative = {
        "no",
        "nope",
        "cancel",
        "stop",
        "don't",
        "do not",
    }

    if text in positive:
        return True

    if text in negative:
        return False

    speak("I need a clear yes or no.")

    return False


def process_command(text: str) -> bool:
    """
    Process one command.

    Returns:
        True  -> keep SUNDAY active
        False -> go to sleep
    """

    # -------------------------------------------------
    # LOCAL CONTROL COMMANDS
    # These must happen BEFORE Ollama.
    # -------------------------------------------------

    if is_exit_command(text):
        speak("Shutting down.")
        raise SystemExit

    if is_sleep_command(text):
        speak("Going quiet.")
        return False

    # -------------------------------------------------
    # NORMAL AI COMMAND
    # -------------------------------------------------

    decision = classify_command(text)

    print("\nTool decision:")
    print(decision)

    tool = decision.get(
        "tool",
        "unknown",
    )

    arguments = decision.get(
        "arguments",
        {},
    )

    # -------------------------------------------------
    # PERMISSION
    # -------------------------------------------------

    if requires_confirmation(tool):
        approved = confirmation_response()

        if not approved:
            speak("Cancelled.")
            return True

    # -------------------------------------------------
    # EXECUTE
    # -------------------------------------------------

    result = execute_tool(
        tool,
        arguments,
    )

    print(f"\nSunday: {result}")

    speak(result)

    return True

def active_loop() -> bool:
    """
    SUNDAY remains active and processes
    commands until the user tells it to sleep.
    """

    while True:

        text = get_voice_command()

        if not text:
            continue

        keep_active = process_command(text)

        if not keep_active:
            return False


def main() -> None:

    print()
    print("========================================")
    print("              SUNDAY")
    print("       LOCAL LAPTOP AI AGENT")
    print("========================================")
    print()
    print("Status: READY")
    print()

    # Start active on launch.
    speak(
        "Hi, I'm Sunday. Do you need anything Sir"
    )

    active = True

    while True:

        try:

            # =========================================
            # ACTIVE MODE
            # =========================================

            if active:

                active = active_loop()

                print()
                print("Sunday is sleeping.")
                print("👏 Clap to wake me.")
                print()

            # =========================================
            # SLEEP MODE
            # =========================================

            else:

                wait_for_clap()

                speak(
                    "I'm awake. What do you need Sir?"
                )

                active = True

        except SystemExit:
            break

        except KeyboardInterrupt:
            print()
            print("Stopping Sunday.")
            break

        except Exception as exc:

            print()
            print(f"ERROR: {exc}")

            try:
                speak(
                    "Something went wrong."
                )
            except Exception:
                pass

            time.sleep(1)


if __name__ == "__main__":
    main()