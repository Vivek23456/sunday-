import time

import numpy as np
import sounddevice as sd


DEVICE = 4

SAMPLE_RATE = 48000
CHANNELS = 2
BLOCK_SIZE = 480

RMS_THRESHOLD = 0.16
PEAK_THRESHOLD = 0.65

MIN_GAP = 0.25
MAX_GAP = 0.60

CLAP_COOLDOWN = 0.25


class DoubleClapDetector:

    def __init__(self):
        self.first_clap = None
        self.last_clap = 0.0
        self.last_rms = 0.0
        self.triggered = False

    def _is_clap(
        self,
        audio: np.ndarray,
    ) -> bool:

        if audio.ndim == 2:
            audio = audio.mean(axis=1)

        audio = audio.astype(
            np.float32,
            copy=False,
        )

        rms = float(
            np.sqrt(
                np.mean(audio * audio)
            )
        )

        peak = float(
            np.max(np.abs(audio))
        )

        if rms < RMS_THRESHOLD:
            return False

        if peak < PEAK_THRESHOLD:
            return False

        # Crest factor:
        # claps tend to have a sharp peak compared
        # with their average energy.
        crest = peak / max(rms, 1e-6)

        if crest < 3.0:
            return False

        # Very long/high-energy blocks are more likely
        # to be music or speech than a clap.
        if rms > 0.75:
            return False

        return True

    def _callback(
        self,
        indata,
        frames,
        time_info,
        status,
    ):
        if status:
            print(
                f"Audio status: {status}"
            )

        now = time.monotonic()

        audio = np.asarray(
            indata,
            dtype=np.float32,
        )

        if not self._is_clap(audio):
            return

        if (
            now - self.last_clap
            < CLAP_COOLDOWN
        ):
            return

        self.last_clap = now

        if self.first_clap is None:

            self.first_clap = now

            print(
                "👏 First clap detected"
            )

            return

        gap = (
            now - self.first_clap
        )

        if (
            MIN_GAP
            <= gap
            <= MAX_GAP
        ):

            print(
                f"👏👏 DOUBLE CLAP "
                f"(gap={gap:.2f}s)"
            )

            self.triggered = True
            self.first_clap = None

            raise sd.CallbackStop()

        # Wrong timing; treat this as a new first clap.
        self.first_clap = now

    def wait(self) -> bool:

        self.triggered = False
        self.first_clap = None
        self.last_clap = 0.0

        print(
            "Waiting for 👏👏 ..."
        )

        try:

            with sd.InputStream(
                device=DEVICE,
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                blocksize=BLOCK_SIZE,
                dtype="float32",
                callback=self._callback,
            ):

                while not self.triggered:
                    sd.sleep(50)

        except sd.CallbackStop:
            pass

        except sd.PortAudioError as exc:
            print(
                f"Wake microphone error: {exc}"
            )
            time.sleep(1)
            return False

        return self.triggered