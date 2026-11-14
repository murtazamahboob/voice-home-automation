"""Offline wake-word detection for the voice home agent.

The wake word is a fixed three-note chime (660 Hz, 880 Hz, 660 Hz — the
"hey home" chime), synthesised as short sine tones. :func:`detect_wake_word`
slides over audio, measures the dominant frequency of each note window with
an FFT, and only fires when all three notes match in order and are loud
enough. It is a toy detector, not a keyword spotter — but the listen →
wake → command loop built on top of it is real, and it runs with no
microphone, no network and no paid API. A real wake-word model can replace
:func:`detect_wake_word` behind the same interface.
"""
from __future__ import annotations

import numpy as np

SAMPLE_RATE = 16000
NOTE_MS = 150
NOTE_SAMPLES = SAMPLE_RATE * NOTE_MS // 1000  # 2400 samples

# The wake-word chime: A5, E5, A5 — "hey home".
WAKE_NOTES = (660.0, 880.0, 660.0)
FREQ_TOLERANCE_HZ = 30.0
RMS_THRESHOLD = 0.05


def rms(samples: np.ndarray) -> float:
    samples = np.asarray(samples, dtype=np.float32)
    return float(np.sqrt(np.mean(samples**2))) if len(samples) else 0.0


def dominant_freq(frame: np.ndarray) -> float:
    """Dominant frequency of one note window, via FFT peak-picking."""
    frame = np.asarray(frame, dtype=np.float32)
    if len(frame) == 0 or rms(frame) < RMS_THRESHOLD:
        return 0.0
    spectrum = np.abs(np.fft.rfft(frame * np.hanning(len(frame)), n=4096))
    freqs = np.fft.rfftfreq(4096, d=1.0 / SAMPLE_RATE)
    return float(freqs[int(np.argmax(spectrum))])


def generate_wake_word() -> np.ndarray:
    """Synthesise the three-note wake-word chime."""
    t = np.arange(NOTE_SAMPLES, dtype=np.float32) / SAMPLE_RATE
    window = np.hanning(NOTE_SAMPLES).astype(np.float32)
    out = np.empty(len(WAKE_NOTES) * NOTE_SAMPLES, dtype=np.float32)
    for i, freq in enumerate(WAKE_NOTES):
        tone = 0.5 * np.sin(2 * np.pi * freq * t) * window
        out[i * NOTE_SAMPLES : (i + 1) * NOTE_SAMPLES] = tone
    return out


def generate_tone(freq: float, ms: int = NOTE_MS) -> np.ndarray:
    """A single sine tone — handy for negative test cases."""
    n = SAMPLE_RATE * ms // 1000
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
    return (0.5 * np.sin(2 * np.pi * freq * t) * np.hanning(n)).astype(np.float32)


def detect_wake_word(samples: np.ndarray) -> bool:
    """True when the audio starts with the wake-word chime, in order."""
    samples = np.asarray(samples, dtype=np.float32)
    needed = len(WAKE_NOTES) * NOTE_SAMPLES
    if len(samples) < needed:
        return False
    for i, expected in enumerate(WAKE_NOTES):
        frame = samples[i * NOTE_SAMPLES : (i + 1) * NOTE_SAMPLES]
        if rms(frame) < RMS_THRESHOLD:
            return False
        if abs(dominant_freq(frame) - expected) > FREQ_TOLERANCE_HZ:
            return False
    return True


def write_wav(path: str, samples: np.ndarray, sample_rate: int = SAMPLE_RATE) -> str:
    """Write float32 mono audio (-1..1) as a 16-bit PCM WAV file."""
    import wave

    pcm = np.clip(np.asarray(samples, dtype=np.float32), -1.0, 1.0)
    pcm = (pcm * 32767).astype(np.int16)
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(pcm.tobytes())
    return path
