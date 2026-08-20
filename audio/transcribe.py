from faster_whisper import WhisperModel


MODEL_SIZE = "small"

print("Loading Whisper model...")

model = WhisperModel(
    MODEL_SIZE,
    device="cuda",
    compute_type="int8_float16",
)

print("Whisper ready.")


def transcribe(audio_file: str) -> str:
    segments, info = model.transcribe(
    audio_file,
    language="en",
    task="transcribe",
    beam_size=1,
    best_of=1,
    temperature=0.0,
    condition_on_previous_text=False,
    vad_filter=False,
    without_timestamps=True,
    no_speech_threshold=0.6,
    log_prob_threshold=-1.0,
    compression_ratio_threshold=2.4,

    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
    ).strip()

    return text


if __name__ == "__main__":
    print(
        transcribe("voice-test.wav")
    )