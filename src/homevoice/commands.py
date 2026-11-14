"""Turn a spoken command (plain text, as a STT transcript would give) into
a structured action the home can apply.

The parser is deliberately forgiving about phrasing — "turn the kitchen
light on", "lights on in the kitchen", "kitchen light on please" all parse —
but strict about the one safety-critical thing: unlocking the front door
needs the spoken PIN, and a missing or wrong PIN is a refusal, never a
guess.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .devices import ROOMS

WAKE_WORDS = ("hey home", "ok home", "hello home")
FAN_SPEEDS = {"off": 0, "low": 1, "medium": 2, "high": 3}
ROOM_ALIASES = {
    "living room": "living room",
    "livingroom": "living room",
    "lounge": "living room",
    "bedroom": "bedroom",
    "bed room": "bedroom",
    "kitchen": "kitchen",
    "bathroom": "bathroom",
    "bath room": "bathroom",
}


@dataclass
class Action:
    kind: str  # light, thermostat, fan, door, blinds, scene, status, energy, timer, unknown
    params: dict = field(default_factory=dict)
    reply: str = ""

    def __repr__(self) -> str:  # short, readable in logs and tests
        return f"Action({self.kind}, {self.params})"


def strip_wake_word(text: str) -> str:
    lowered = text.strip().lower()
    for wake in WAKE_WORDS:
        if lowered.startswith(wake):
            return lowered[len(wake):].strip(" ,")
    return lowered


def find_room(text: str) -> str | None:
    for alias, room in ROOM_ALIASES.items():
        if alias in text:
            return room
    if "all lights" in text or "every light" in text or "all the lights" in text:
        return "all"
    return None


def _number(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _pin(text: str) -> str | None:
    match = re.search(r"pin\s+(\d{4})", text)
    return match.group(1) if match else None


def parse(text: str) -> Action:
    """Parse one command into an Action. Never raises on odd input."""
    raw = text.strip()
    if not raw:
        return Action("unknown", reply="I didn't hear anything — try a command.")
    text = strip_wake_word(raw)

    # -- scenes ---------------------------------------------------------
    for scene in ("good night", "movie night", "good morning", "away", "all off"):
        if scene in text:
            if scene == "all off":
                return Action("scene", {"scene": "all off"}, "Turning everything off.")
            return Action("scene", {"scene": scene}, f"Setting the {scene} scene.")

    # -- status / energy ------------------------------------------------
    if any(p in text for p in ("how is the house", "house status", "status", "what is on", "what's on")):
        return Action("status", reply="Here is the house status.")
    if "energy" in text or "power" in text or "how much electricity" in text:
        return Action("energy", reply="Here is the energy use.")

    # -- timers: "turn off the bedroom light in 5 minutes" --------------
    timer_match = re.search(r"in (\d+)\s*(minute|minutes|second|seconds)", text)
    if timer_match and ("turn off" in text or "turn on" in text or "set " in text):
        amount, unit = int(timer_match.group(1)), timer_match.group(2)
        base_unit = "minute" if "minute" in unit else "second"
        delay = amount * 60 if base_unit == "minute" else amount
        inner = re.sub(r"\s*in \d+\s*(minute|minutes|second|seconds)\s*", "", text).strip()
        inner_action = parse(inner)
        if inner_action.kind == "unknown":
            return Action("unknown", reply="I understood the timer, but not the action to run.")
        unit_word = base_unit if amount == 1 else base_unit + "s"
        return Action(
            "timer",
            {"delay_s": delay, "action": inner_action},
            f"Okay, I will do that in {amount} {unit_word}.",
        )

    # -- door (PIN-gated) -----------------------------------------------
    if "door" in text or "front door" in text:
        if "unlock" in text:
            pin = _pin(text)
            return Action("door", {"locked": False, "pin": pin},
                          "Unlocking the front door." if pin else "I need the PIN to unlock the door.")
        if "lock" in text:
            return Action("door", {"locked": True}, "Locking the front door.")

    # -- blinds ---------------------------------------------------------
    if "blind" in text:
        room = find_room(text) or "living room"
        if "open" in text:
            pct = _number(text)
            return Action("blinds", {"room": room, "open_pct": int(pct) if pct is not None else 100},
                          f"Opening the {room} blinds.")
        if "close" in text or "shut" in text:
            return Action("blinds", {"room": room, "open_pct": 0},
                          f"Closing the {room} blinds.")
        pct = _number(text)
        if pct is not None:
            return Action("blinds", {"room": room, "open_pct": int(pct)},
                          f"Setting the {room} blinds to {int(pct)} percent.")

    # -- thermostat -----------------------------------------------------
    if "thermostat" in text or "temperature" in text or "degrees" in text or "heating" in text:
        temp = _number(text)
        if "increase" in text or "raise" in text or "up" in text:
            delta = temp if temp is not None else 1.0
            return Action("thermostat", {"delta": delta}, f"Raising the temperature by {delta:g} degrees.")
        if "decrease" in text or "lower" in text or "down" in text:
            delta = temp if temp is not None else 1.0
            return Action("thermostat", {"delta": -delta}, f"Lowering the temperature by {delta:g} degrees.")
        if temp is not None:
            return Action("thermostat", {"target_c": temp}, f"Setting the thermostat to {temp:g} degrees.")
        if "off" in text:
            return Action("thermostat", {"mode": "off"}, "Turning the thermostat off.")
        if "heat" in text:
            return Action("thermostat", {"mode": "heat"}, "Setting the thermostat to heat.")
        if "cool" in text:
            return Action("thermostat", {"mode": "cool"}, "Setting the thermostat to cool.")

    # -- fan ------------------------------------------------------------
    if "fan" in text:
        for name, speed in FAN_SPEEDS.items():
            if name in text:
                return Action("fan", {"speed": speed}, f"Setting the fan to {name}.")
        if "on" in text:
            return Action("fan", {"speed": 2}, "Turning the fan to medium.")
        if "off" in text:
            return Action("fan", {"speed": 0}, "Turning the fan off.")

    # -- lights ---------------------------------------------------------
    if "light" in text or "lights" in text or "lamp" in text:
        room = find_room(text) or "all"
        pct = _number(text)
        if "dim" in text:
            delta = -(pct if pct is not None else 20)
            return Action("light", {"room": room, "delta": delta},
                          f"Dimming the {room} light by {abs(delta):g} percent.")
        if "brighten" in text or "brighter" in text:
            delta = pct if pct is not None else 20
            return Action("light", {"room": room, "delta": delta},
                          f"Brightening the {room} light by {delta:g} percent.")
        if pct is not None and ("percent" in text or "%" in text or "brightness" in text):
            return Action("light", {"room": room, "on": True, "brightness": int(pct)},
                          f"Setting the {room} light to {int(pct)} percent.")
        if "off" in text:
            return Action("light", {"room": room, "on": False},
                          f"Turning off the {room} light.")
        if "on" in text:
            return Action("light", {"room": room, "on": True},
                          f"Turning on the {room} light.")
        return Action("light", {"room": room, "on": True},
                      f"Turning on the {room} light.")

    return Action(
        "unknown",
        reply="Sorry, I didn't understand — try 'turn on the kitchen light' or 'set the thermostat to 22 degrees'.",
    )
