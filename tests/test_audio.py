"""Tests for the offline wake-word detector."""
import numpy as np

from homevoice.audio import (
    detect_wake_word,
    dominant_freq,
    generate_tone,
    generate_wake_word,
)


def test_wake_word_detected():
    assert detect_wake_word(generate_wake_word()) is True


def test_silence_not_detected():
    assert detect_wake_word(np.zeros(7200, dtype=np.float32)) is False


def test_wrong_notes_not_detected():
    # Same rhythm, wrong pitches.
    samples = np.concatenate([generate_tone(440.0), generate_tone(440.0), generate_tone(440.0)])
    assert detect_wake_word(samples) is False


def test_wrong_order_not_detected():
    samples = np.concatenate([generate_tone(880.0), generate_tone(660.0), generate_tone(660.0)])
    assert detect_wake_word(samples) is False


def test_too_short_not_detected():
    assert detect_wake_word(generate_wake_word()[:3000]) is False


def test_dominant_freq_matches_tone():
    assert abs(dominant_freq(generate_tone(880.0)) - 880.0) < 30.0


def test_quiet_chime_not_detected():
    assert detect_wake_word(generate_wake_word() * 0.01) is False


def test_chime_with_trailing_noise_still_detected():
    samples = np.concatenate([generate_wake_word(), np.zeros(2400, dtype=np.float32)])
    assert detect_wake_word(samples) is True
