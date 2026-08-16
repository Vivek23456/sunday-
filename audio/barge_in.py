import time

import numpy as np
import sounddevice as sd


DEVICE = 4

SAMPLE_RATE = 48000
BLOCK_SIZE = 512

RMS_THRESHOLD = 0.025


def listen_for_interrupt(
    timeout: float = 20.0,
) -> bool:

    detected = False
    start_time = time.monotonic()

    def callback(
        indata,
        frames,
        time_info,
        status,
    ):
        nonlocal detected

        if status:
            return

        # Handle whatever channel layout the device provides.
        audio = np.asarray(
            indata,
            dtype=np.float32,
        )

        if audio.ndim == 2:
            audio = audio.mean(axis=1)

        rms = float(
            np.sqrt(
                np.mean(
                    audio * audio
                )
            )
        )

        if rms >= RMS_THRESHOLD:
            detected = True
            raise sd.CallbackStop()

    try:

        # IMPORTANT:
        # Use the exact input channel count supported
        # by the C-Media device.
        device_info = sd.query_devices(
            DEVICE
        )

        max_input_channels = int(
            device_info["max_input_channels"]
        )

        if max_input_channels < 1:
            print(
                "Barge-in microphone has no "
                "input channels."
            )
            return False

        with sd.InputStream(
            device=DEVICE,
            samplerate=SAMPLE_RATE,
            channels=1,
            blocksize=BLOCK_SIZE,
            dtype="float32",
            callback=callback,
        ):

            while not detected:

                elapsed = (
                    time.monotonic()
                    - start_time
                )

                if elapsed >= timeout:
                    break

                sd.sleep(20)

    except sd.CallbackStop:
        pass

    except sd.PortAudioError as exc:
        print(
            f"Barge-in microphone error: {exc}"
        )
        return False

    return detected