import sys
import threading
import time

from PySide6.QtWidgets import QApplication

from audio.barge_in import listen_for_interrupt
from audio.record import record_command
from audio.transcribe import transcribe
from audio.tts import speak, stop_speaking

from agent.permissions import requires_confirmation
from agent.router import classify_command, execute_tool

from ui.main_window import SundayWindow
from ui.wake_detector import DoubleClapDetector
from ui.hand_gesture import HandGestureController


COMMAND_FILE = "command.wav"


SLEEP_COMMANDS = {
    "shut up",
    "stop listening",
    "go to sleep",
    "sleep",
    "be quiet",
    "quiet",
    "bye",
    "goodbye",
}


EXIT_COMMANDS = {
    "shutdown sunday",
    "shut down sunday",
    "exit sunday",
    "quit sunday",
}


def normalize_command(
    text: str,
) -> str:

    text = (
        text
        .lower()
        .strip()
        .strip(".,!?")
    )

    replacements = {
        "open various code": "open vscode",
        "open various codes": "open vscode",
        "open vs code": "open vscode",
        "open visual studio code": "open vscode",
        "launch visual studio code": "open vscode",
        "launch vs code": "open vscode",
    }

    return replacements.get(
        text,
        text,
    )


def is_sleep_command(
    text: str,
) -> bool:

    normalized = (
        text
        .lower()
        .strip()
        .strip(".,!?")
    )

    return any(
        phrase in normalized
        for phrase in SLEEP_COMMANDS
    )


def is_exit_command(
    text: str,
) -> bool:

    normalized = (
        text
        .lower()
        .strip()
        .strip(".,!?")
    )

    return any(
        phrase in normalized
        for phrase in EXIT_COMMANDS
    )


def valid_transcription(
    text: str,
) -> bool:

    if not text:
        return False

    words = text.lower().split()

    if not words:
        return False

    if len(words) >= 6:

        unique_words = set(
            words
        )

        if len(unique_words) <= 3:
            return False

    if len(words) > 20:
        return False

    return True


def get_voice_command() -> str | None:

    audio_file = record_command(
        COMMAND_FILE
    )

    if not audio_file:
        return None

    print(
        "\nTranscribing..."
    )

    text = transcribe(
        audio_file
    ).strip()

    if not valid_transcription(
        text
    ):

        print(
            "Ignoring unreliable transcription."
        )

        return None

    text = normalize_command(
        text
    )

    print(
        f"You: {text}"
    )

    return text


def confirmation_response() -> bool:

    speak(
        "This action requires confirmation. "
        "Should I proceed?"
    )

    response = get_voice_command()

    if not response:
        return False

    text = (
        response
        .lower()
        .strip()
        .strip(".,!?")
    )

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
        "correct",
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

    speak(
        "I need a clear yes or no."
    )

    return False


def speak_with_barge_in(
    text: str,
    ui: "SundayWindow",
) -> bool:

    ui.set_status(
        "SPEAKING"
    )

    interrupted = False

    def monitor():

        nonlocal interrupted

        interrupted = (
            listen_for_interrupt(
                timeout=30.0
            )
        )

        if interrupted:
            stop_speaking()

    monitor_thread = threading.Thread(
        target=monitor,
        daemon=True,
        name="sunday-barge-in",
    )

    monitor_thread.start()

    try:

        speak(text)

    finally:

        stop_speaking()

    if interrupted:

        print(
            "SUNDAY interrupted by user."
        )

        return False

    return True


def process_command(
    text: str,
    ui: "SundayWindow",
) -> bool:

    text = normalize_command(
        text
    )

    # =========================================================
    # LOCAL CONTROL
    # =========================================================

    if is_exit_command(text):

        speak(
            "Shutting down."
        )

        ui.set_status(
            "OFFLINE"
        )

        raise SystemExit

    if is_sleep_command(text):

        speak(
            "Going quiet."
        )

        ui.set_status(
            "SLEEPING"
        )

        return False

    # =========================================================
    # THINKING
    # =========================================================

    ui.set_status(
        "THINKING"
    )

    decision = classify_command(
        text
    )

    print()
    print(
        "Tool decision:"
    )

    print(
        decision
    )

    tool = decision.get(
        "tool",
        "unknown",
    )

    arguments = decision.get(
        "arguments",
        {},
    )

    # =========================================================
    # PERMISSION
    # =========================================================

    if requires_confirmation(
        tool
    ):

        ui.set_status(
            "CONFIRMING"
        )

        approved = (
            confirmation_response()
        )

        if not approved:

            speak(
                "Cancelled."
            )

            ui.set_status(
                "LISTENING"
            )

            return True

    # =========================================================
    # EXECUTE
    # =========================================================

    ui.set_status(
        "WORKING"
    )

    result = execute_tool(
        tool,
        arguments,
    )

    print(
        f"\nSunday: {result}"
    )

    # =========================================================
    # SPEAK
    # =========================================================

    completed = (
        speak_with_barge_in(
            result,
            ui,
        )
    )

    if not completed:

        ui.set_status(
            "LISTENING"
        )

        return True

    # =========================================================
    # BACK TO LISTENING
    # =========================================================

    ui.set_status(
        "LISTENING"
    )

    return True


def active_loop(
    ui: "SundayWindow",
) -> bool:

    ui.set_status(
        "LISTENING"
    )

    while True:

        text = get_voice_command()

        if not text:
            continue

        keep_active = process_command(
            text,
            ui,
        )

        if not keep_active:
            return False


def run_agent(
    ui: "SundayWindow",
):

    # ---------------------------------------------------------
    # DOUBLE-CLAP WAKE CONTROLLER
    #
    # This stays independent from the camera gesture system.
    # 👏👏 remains the SUNDAY wake gesture.
    # ---------------------------------------------------------

    detector = (
        DoubleClapDetector()
    )

    active = False

    ui.set_status(
        "SLEEPING"
    )

    while True:

        try:

            # =================================================
            # SLEEPING
            # =================================================

            if not active:

                detected = detector.wait()

                if not detected:
                    continue

                ui.set_status(
                    "WAKING"
                )

                speak(
                    "I'm awake. "
                    "What do you need?"
                )

                active = True

            # =================================================
            # ACTIVE
            # =================================================

            else:

                active = active_loop(
                    ui
                )

                if not active:

                    ui.set_status(
                        "SLEEPING"
                    )

        except SystemExit:

            break

        except Exception as exc:

            print(
                f"ERROR: {exc}"
            )

            try:

                speak(
                    "Something went wrong."
                )

            except Exception:
                pass

            ui.set_status(
                "ERROR"
            )

            time.sleep(1)

            ui.set_status(
                "SLEEPING"
            )

            active = False


def start_hand_gesture_controller():
    """
    Start the camera gesture controller.

    The camera subsystem is intentionally isolated from the
    voice/wake loop so a camera/model failure cannot prevent
    SUNDAY from starting.
    """

    try:

        controller = (
            HandGestureController()
        )

        controller.start()

        print(
            "Hand gesture controller started."
        )

        return controller

    except Exception as exc:

        print(
            "Hand gesture controller "
            f"could not start: {exc}"
        )

        return None


def stop_hand_gesture_controller(
    controller,
):
    """
    Stop the camera gesture controller cleanly.
    """

    if controller is None:
        return

    try:

        controller.stop()

        print(
            "Hand gesture controller stopped."
        )

    except Exception as exc:

        print(
            "Gesture shutdown error:",
            exc,
        )


def main():

    app = QApplication(
        sys.argv
    )

    # =========================================================
    # DESKTOP UI
    # =========================================================

    window = SundayWindow()

    window.set_status(
        "SLEEPING"
    )

    window.show()

    # =========================================================
    # CAMERA HAND GESTURE CONTROLLER
    #
    # 👏👏 is still handled by DoubleClapDetector.
    #
    # 🖐️ Open Palm  -> display OFF
    # ✊ Closed Fist -> display ON
    # =========================================================

    gesture_controller = (
        start_hand_gesture_controller()
    )

    # =========================================================
    # VOICE AGENT WORKER
    # =========================================================

    worker = threading.Thread(
        target=run_agent,
        args=(window,),
        daemon=True,
        name="sunday-agent",
    )

    worker.start()

    # =========================================================
    # QT EVENT LOOP
    # =========================================================

    try:

        return_code = app.exec()

    except KeyboardInterrupt:

        print(
            "\nStopping SUNDAY."
        )

        return_code = 0

    finally:

        # -----------------------------------------------------
        # Stop camera worker first.
        # -----------------------------------------------------

        stop_hand_gesture_controller(
            gesture_controller
        )

        # -----------------------------------------------------
        # Stop any active TTS.
        # -----------------------------------------------------

        try:

            stop_speaking()

        except Exception:
            pass

    sys.exit(
        return_code
    )


if __name__ == "__main__":
    main()