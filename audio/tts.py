import subprocess
import tempfile
import threading
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

PIPER_BIN = (
    BASE_DIR
    / "piper-bin"
    / "piper"
    / "piper"
)

VOICE_MODEL = (
    BASE_DIR
    / "voices"
    / "en_US-lessac-medium.onnx"
)


class PiperTTS:
    def __init__(self):
        self.play_process = None
        self.lock = threading.Lock()

    def speak(self, text: str) -> None:
        text = text.strip()

        if not text:
            return

        if not PIPER_BIN.exists():
            raise FileNotFoundError(
                f"Piper not found: {PIPER_BIN}"
            )

        if not VOICE_MODEL.exists():
            raise FileNotFoundError(
                f"Voice model not found: {VOICE_MODEL}"
            )

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        ) as temp:
            output_file = Path(temp.name)

        try:
            subprocess.run(
                [
                    str(PIPER_BIN),
                    "--model",
                    str(VOICE_MODEL),
                    "--output_file",
                    str(output_file),
                ],
                input=text.encode("utf-8"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )

            with self.lock:
                self.play_process = subprocess.Popen(
                    [
                        "aplay",
                        "-q",
                        str(output_file),
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            self.play_process.wait()

        finally:
            with self.lock:
                self.play_process = None

            output_file.unlink(
                missing_ok=True
            )

    def stop(self) -> None:
        with self.lock:
            process = self.play_process

        if process is None:
            return

        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=0.5)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass

        with self.lock:
            self.play_process = None


tts = PiperTTS()


def speak(text: str) -> None:
    tts.speak(text)


def stop_speaking() -> None:
    tts.stop()