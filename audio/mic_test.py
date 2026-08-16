import time
import numpy as np
import sounddevice as sd

DEVICE = 11
SAMPLE_RATE = 44100
BLOCK_SIZE = 1024
DURATION = 10


rms_values = []
peak_values = []


print("Recording microphone levels for 10 seconds.")
print()
print("Do this:")
print("0-3s  : stay silent")
print("3-6s  : speak normally")
print("6-7s  : clap once")
print("7-10s : stay silent")
print()


def callback(indata, frames, time_info, status):
    if status:
        print(f"Audio status: {status}")

    audio = indata[:, 0].astype(np.float32)

    rms = float(np.sqrt(np.mean(audio * audio)))
    peak = float(np.max(np.abs(audio)))

    rms_values.append(rms)
    peak_values.append(peak)


with sd.InputStream(
    device=DEVICE,
    samplerate=SAMPLE_RATE,
    channels=1,
    blocksize=BLOCK_SIZE,
    dtype="float32",
    callback=callback,
):
    time.sleep(DURATION)


print("\n--- RESULTS ---")

print(
    f"RMS min : {min(rms_values):.5f}"
)

print(
    f"RMS avg : {np.mean(rms_values):.5f}"
)

print(
    f"RMS max : {max(rms_values):.5f}"
)

print(
    f"PEAK min: {min(peak_values):.5f}"
)

print(
    f"PEAK max: {max(peak_values):.5f}"
)