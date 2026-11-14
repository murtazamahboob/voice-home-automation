"""Voice Home Automation — voice commands for a simulated smart home.

Offline, stdlib + NumPy only: a three-note wake-word chime, a forgiving
natural-language command parser, PIN-gated door unlock, named scenes,
timers on a virtual clock, and a live energy report.
"""
from .agent import VoiceHomeAgent
from .audio import detect_wake_word, generate_wake_word

__all__ = ["VoiceHomeAgent", "detect_wake_word", "generate_wake_word"]
__version__ = "1.0.0"
