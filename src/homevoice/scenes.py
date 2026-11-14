"""Named scenes: one phrase, a whole-house change.

Each scene is a list of the same low-level actions the parser produces, so
scenes and single commands can never disagree about what a device does.
"""
from __future__ import annotations

SCENES: dict[str, list[dict]] = {
    "good night": [
        {"kind": "light", "params": {"room": "all", "on": False}},
        {"kind": "door", "params": {"locked": True}},
        {"kind": "thermostat", "params": {"target_c": 19.0}},
        {"kind": "blinds", "params": {"room": "all", "open_pct": 0}},
        {"kind": "fan", "params": {"speed": 0}},
    ],
    "movie night": [
        {"kind": "light", "params": {"room": "living room", "on": True, "brightness": 20}},
        {"kind": "light", "params": {"room": "bedroom", "on": False}},
        {"kind": "light", "params": {"room": "kitchen", "on": False}},
        {"kind": "blinds", "params": {"room": "living room", "open_pct": 0}},
    ],
    "good morning": [
        {"kind": "light", "params": {"room": "bedroom", "on": True, "brightness": 80}},
        {"kind": "blinds", "params": {"room": "all", "open_pct": 100}},
        {"kind": "thermostat", "params": {"target_c": 22.0}},
    ],
    "away": [
        {"kind": "light", "params": {"room": "all", "on": False}},
        {"kind": "door", "params": {"locked": True}},
        {"kind": "thermostat", "params": {"target_c": 17.0}},
        {"kind": "fan", "params": {"speed": 0}},
    ],
    "all off": [
        {"kind": "light", "params": {"room": "all", "on": False}},
        {"kind": "thermostat", "params": {"mode": "off"}},
        {"kind": "fan", "params": {"speed": 0}},
    ],
}


def scene_actions(name: str) -> list[dict]:
    return [dict(a, params=dict(a["params"])) for a in SCENES[name]]
