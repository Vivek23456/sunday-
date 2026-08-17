import collections
import time

import numpy as np
import sounddevice as sd
import soundfile as sf
import webrtcvad
from scipy.signal import resample_poly


# ============================================================
# MICROPHONE
# ============================================================

DEVICE = "pipewire"

INPUT_RATE = 48000
OUTPUT_RATE = 16000

CHANNELS = 1

FRAME_MS = 20
FRAME_SAMPLES = int(
    INPUT_RATE * FRAME_MS / 1000
)


# ============================================================
# SPEECH DETECTION
# ============================================================

VAD_MODE = 1

PRE_ROLL_MS = 300
MIN_SPEECH_MS = 250
END_SILENCE_MS = 1000

START_TIMEOUT_SECONDS = 3.0
MAX_RECORDING_SECONDS = 6.0


vad = webrtcvad.Vad(VAD_MODE)


def resample_to_16k(
    audio: np.ndarray,
) -> np.ndarray:
    return resample_poly(
        audio,
        up=1,
        down=3,
    ).astype(np.float32)


def to_pcm16(
    audio: np.ndarray,
) -> bytes:
    audio = np.clip(
        audio,
        -1.0,
        1.0,
    )

    return (
        audio * 32767.0
    ).astype(
        np.int16
    ).tobytes()


def record_command(
    output_file: str = "command.wav",
) -> str | None:

    print()
    print("🎤 Listening...")
    print(
        f"Using input device: {DEVICE}"
    )

    queue: collections.deque[np.ndarray] = (
        collections.deque()
    )

    recorded: list[np.ndarray] = []

    pre_roll = collections.deque(
        maxlen=max(
            1,
            PRE_ROLL_MS // FRAME_MS,
        )
    )

    speech_started = False
    speech_ms = 0
    silence_ms = 0

    start_time = time.monotonic()

    def callback(
        indata,
        frames,
        time_info,
        status,
    ):

        if status:
            print(
                f"\nAudio status: {status}"
            )

        queue.append(
            indata[:, 0]
            .astype(np.float32)
            .copy()
        )

    try:

        with sd.InputStream(
            device=DEVICE,
            samplerate=INPUT_RATE,
            channels=CHANNELS,
            blocksize=FRAME_SAMPLES,
            dtype="float32",
            callback=callback,
        ):

            while True:

                if not queue:
                    time.sleep(0.005)
                    continue

                frame = queue.popleft()

                if len(frame) != FRAME_SAMPLES:
                    continue

                # ------------------------------------------------
                # 48 kHz -> 16 kHz for WebRTC VAD
                # ------------------------------------------------

                frame_16k = resample_to_16k(
                    frame
                )

                pcm = to_pcm16(
                    frame_16k
                )

                is_speech = vad.is_speech(
                    pcm,
                    OUTPUT_RATE,
                )

                # ------------------------------------------------
                # WAITING FOR SPEECH
                # ------------------------------------------------

                if not speech_started:

                    pre_roll.append(
                        frame
                    )

                    if is_speech:

                        speech_ms += FRAME_MS

                        if (
                            speech_ms
                            >= MIN_SPEECH_MS
                        ):

                            speech_started = True

                            recorded.extend(
                                list(pre_roll)
                            )

                            silence_ms = 0

                    else:

                        speech_ms = 0

                # ------------------------------------------------
                # SPEECH IN PROGRESS
                # ------------------------------------------------

                else:

                    recorded.append(
                        frame
                    )

                    if is_speech:

                        silence_ms = 0

                    else:

                        silence_ms += FRAME_MS

                        if (
                            silence_ms
                            >= END_SILENCE_MS
                        ):
                            break

                # ------------------------------------------------
                # TIMEOUTS
                # ------------------------------------------------

                elapsed = (
                    time.monotonic()
                    - start_time
                )

                if (
                    not speech_started
                    and elapsed
                    >= START_TIMEOUT_SECONDS
                ):

                    print(
                        "No speech detected."
                    )

                    return None

                if (
                    elapsed
                    >= MAX_RECORDING_SECONDS
                ):
                    break

    except sd.PortAudioError as exc:

        print(
            f"Microphone error: {exc}"
        )

        return None

    if not recorded:

        print(
            "No speech captured."
        )

        return None

    # ------------------------------------------------------------
    # COMBINE 48 kHz AUDIO
    # ------------------------------------------------------------

    audio_48k = np.concatenate(
        recorded
    )

    # ------------------------------------------------------------
    # RESAMPLE 48 kHz -> 16 kHz
    # ------------------------------------------------------------

    audio_16k = resample_to_16k(
        audio_48k
    )

    # ------------------------------------------------------------
    # GENTLE NORMALIZATION
    # ------------------------------------------------------------

    peak = float(
        np.max(
            np.abs(audio_16k)
        )
    )

    if peak > 0.0:

        target_peak = 0.92

        gain = min(
            target_peak / peak,
            2.0,
        )

        audio_16k *= gain

    # ------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------

    sf.write(
        output_file,
        audio_16k,
        OUTPUT_RATE,
        subtype="PCM_16",
    )

    duration = (
        len(audio_16k)
        / OUTPUT_RATE
    )

    print(
        f"✓ Recording finished "
        f"({duration:.2f}s)"
    )

    return output_file


if __name__ == "__main__":
    record_command(
        "voice-test.wav"
    )