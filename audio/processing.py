import numpy as np


def normalize_audio(audio: np.ndarray) -> np.ndarray:
    audio = audio.astype(np.float32)

    peak = np.max(np.abs(audio))

    if peak <= 0:
        return audio

    target = 0.85

    gain = min(target / peak, 2.0)

    return audio * gain


def remove_dc(audio: np.ndarray) -> np.ndarray:
    return audio - np.mean(audio)


def process_audio(audio: np.ndarray) -> np.ndarray:
    audio = remove_dc(audio)
    audio = normalize_audio(audio)

    return np.clip(audio, -1.0, 1.0)
