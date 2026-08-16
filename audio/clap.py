import time

import numpy as np
import sounddevice as sd


DEVICE = 4
SAMPLE_RATE = 44100
BLOCK_SIZE = 512

RMS_THRESHOLD = 0.12
PEAK_THRESHOLD = 0.45
COOLDOWN = 1.0


def wait_for_clap() -> bool:
    """
    Block until a clap is detected.
    Returns True exactly once per clap.
    """

    detected = False
    last_clap = 0.0

    def callback(indata, frames, time_info, status):
        nonlocal detected, last_clap

        if status:
            print(f"\nAudio status: {status}")

        audio = indata[:, 0].astype(np.float32)

        rms = float(
            np.sqrt(np.mean(audio * audio))
        )

        peak = float(
            np.max(np.abs(audio))
        )

        now = time.monotonic()

        if (
            rms >= RMS_THRESHOLD
            and peak >= PEAK_THRESHOLD
            and now - last_clap >= COOLDOWN
        ):
            last_clap = now
            detected = True

            print()
            print("👏 CLAP DETECTED")
            print(f"   RMS  : {rms:.4f}")
            print(f"   PEAK : {peak:.4f}")

    print("Waiting for clap...")

    with sd.InputStream(
        device=DEVICE,
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        channels=1,
        dtype="float32",
        callback=callback,
    ):
        while not detected:
            time.sleep(0.05)

    return True


# Keep standalone testing.
if __name__ == "__main__":
    while True:
        wait_for_clap()