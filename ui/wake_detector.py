import time

import numpy as np
import sounddevice as sd


DEVICE = "pipewire"

SAMPLE_RATE = 16000
BLOCK_SIZE = 160

RMS_THRESHOLD = 0.055
PEAK_THRESHOLD = 0.18
CREST_THRESHOLD = 2.5

MIN_GAP = 0.12
MAX_GAP = 0.55

CLAP_COOLDOWN = 0.10


class DoubleClapDetector:

    def __init__(self):
        self.first_clap = 0.0
        self.last_clap = 0.0
        self.triggered = False

    def _is_clap(self, audio: np.ndarray) -> bool:
        if audio.ndim == 2:
            audio = audio[:, 0]

        rms = float(
            np.sqrt(
                np.mean(audio * audio)
            )
        )

        if rms < RMS_THRESHOLD:
            return False

        peak = float(
            np.max(np.abs(audio))
        )

        if peak < PEAK_THRESHOLD:
            return False

        crest = peak / max(rms, 1e-6)

        return crest >= CREST_THRESHOLD

    def _callback(
        self,
        indata,
        frames,
        time_info,
        status,
    ):
        if status:
            return

        now = time.monotonic()

        if now - self.last_clap < CLAP_COOLDOWN:
            return

        audio = np.asarray(
            indata,
            dtype=np.float32,
        )

        if not self._is_clap(audio):
            return

        self.last_clap = now

        if self.first_clap == 0.0:
            self.first_clap = now
            return

        gap = now - self.first_clap

        if MIN_GAP <= gap <= MAX_GAP:
            self.triggered = True
            self.first_clap = 0.0
            raise sd.CallbackStop()

        self.first_clap = now

    def wait(self) -> bool:
        self.triggered = False
        self.first_clap = 0.0
        self.last_clap = 0.0

        print("Waiting for 👏👏 ...")

        try:
            with sd.InputStream(
                device=DEVICE,
                samplerate=SAMPLE_RATE,
                channels=1,
                blocksize=BLOCK_SIZE,
                dtype="float32",
                latency="low",
                callback=self._callback,
            ):
                while not self.triggered:
                    sd.sleep(10)

        except sd.PortAudioError as exc:
            print(f"Wake microphone error: {exc}")
            time.sleep(0.5)
            return False

        print("👏👏 DOUBLE CLAP")

        return True


if __name__ == "__main__":
    detector = DoubleClapDetector()

    while True:
        detector.wait()