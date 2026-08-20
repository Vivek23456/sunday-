import time

import numpy as np
import sounddevice as sd


DEVICE = 4

SAMPLE_RATE = 44100
BLOCK_SIZE = 256

NOISE_CALIBRATION_SECONDS = 1.5

CLAP_MULTIPLIER = 3.0
MIN_CLAP_RMS = 0.025
MIN_CLAP_PEAK = 0.12

MIN_CLAP_GAP = 0.16
MAX_CLAP_GAP = 0.75

CLAP_COOLDOWN = 0.15


def _calculate_levels(audio: np.ndarray) -> tuple[float, float]:
    rms = float(
        np.sqrt(
            np.mean(
                audio * audio
            )
        )
    )

    peak = float(
        np.max(
            np.abs(audio)
        )
    )

    return rms, peak


def _calibrate_noise() -> float:
    levels = []

    def callback(indata, frames, time_info, status):
        if status:
            print(
                f"\nAudio status: {status}"
            )

        audio = (
            indata[:, 0]
            .astype(np.float32)
        )

        rms, _ = _calculate_levels(
            audio
        )

        levels.append(rms)

    print(
        "Calibrating microphone noise..."
    )

    with sd.InputStream(
        device=DEVICE,
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        channels=1,
        dtype="float32",
        callback=callback,
    ):
        time.sleep(
            NOISE_CALIBRATION_SECONDS
        )

    if not levels:
        return MIN_CLAP_RMS

    noise_floor = float(
        np.percentile(
            levels,
            80,
        )
    )

    return max(
        noise_floor,
        MIN_CLAP_RMS,
    )


def wait_for_double_clap() -> bool:
    noise_floor = _calibrate_noise()

    rms_threshold = max(
        MIN_CLAP_RMS,
        noise_floor * CLAP_MULTIPLIER,
    )

    print(
        f"Noise floor : {noise_floor:.4f}"
    )

    print(
        f"RMS threshold : {rms_threshold:.4f}"
    )

    first_clap_time = None
    last_candidate_time = 0.0

    detected = False

    def callback(indata, frames, time_info, status):
        nonlocal first_clap_time
        nonlocal last_candidate_time
        nonlocal detected

        if status:
            print(
                f"\nAudio status: {status}"
            )

        audio = (
            indata[:, 0]
            .astype(np.float32)
        )

        rms, peak = _calculate_levels(
            audio
        )

        now = time.monotonic()

        if now - last_candidate_time < CLAP_COOLDOWN:
            return

        is_clap = (
            rms >= rms_threshold
            and peak >= MIN_CLAP_PEAK
        )

        if not is_clap:
            if (
                first_clap_time is not None
                and now - first_clap_time
                > MAX_CLAP_GAP
            ):
                first_clap_time = None

            return

        last_candidate_time = now

        print(
            f"\n👏 Clap candidate"
            f"  RMS={rms:.4f}"
            f"  PEAK={peak:.4f}"
        )

        if first_clap_time is None:
            first_clap_time = now

            print(
                "👏 First clap detected"
            )

            return

        gap = now - first_clap_time

        if MIN_CLAP_GAP <= gap <= MAX_CLAP_GAP:
            print(
                f"👏👏 DOUBLE CLAP"
                f" (gap={gap:.2f}s)"
            )

            detected = True

        else:
            first_clap_time = now

    print(
        "Waiting for 👏👏 ..."
    )

    with sd.InputStream(
        device=DEVICE,
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        channels=1,
        dtype="float32",
        callback=callback,
    ):
        while not detected:
            time.sleep(0.02)

    return True


if __name__ == "__main__":
    while True:
        wait_for_double_clap()