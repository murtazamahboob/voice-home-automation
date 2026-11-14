"""Voice Home Agent — the listen → wake → command loop.

The agent owns the home state, a virtual clock (so timers are testable
without waiting), and an audit log of everything it did and why. It never
executes a door unlock without the right PIN, and every command — understood
or not — is logged.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .audio import detect_wake_word
from .commands import Action, parse
from .devices import HomeState
from .scenes import SCENES, scene_actions

DEFAULT_PIN = "1234"


@dataclass
class Timer:
    due_s: float
    action: Action
    label: str


@dataclass
class AuditEntry:
    at_s: float
    heard: str
    reply: str


class VoiceHomeAgent:
    """One house, one voice agent. All state lives here."""

    def __init__(self, pin: str = DEFAULT_PIN):
        self.home = HomeState()
        self.pin = pin
        self.clock_s = 0.0
        self.timers: list[Timer] = []
        self.audit: list[AuditEntry] = []
        self.awake = False

    # -- listening ------------------------------------------------------
    def hear_audio(self, samples: np.ndarray) -> bool:
        """Wake-word check on raw audio. Sets ``awake`` for the next command."""
        self.awake = detect_wake_word(samples)
        return self.awake

    # -- commands -------------------------------------------------------
    def handle_command(self, text: str) -> str:
        """Parse and execute one spoken command; returns the spoken reply."""
        action = parse(text)
        reply = self.execute(action, heard=text)
        self.audit.append(AuditEntry(self.clock_s, text.strip(), reply))
        return reply

    def execute(self, action: Action, heard: str = "") -> str:
        kind, p = action.kind, action.params
        if kind == "light":
            if "delta" in p:
                self.home.dim_light(p["room"], p["delta"])
            else:
                self.home.set_light(p["room"], p["on"], p.get("brightness"))
            return action.reply
        if kind == "thermostat":
            if "delta" in p:
                self.home.adjust_thermostat(p["delta"])
            elif "target_c" in p:
                self.home.set_thermostat(p["target_c"])
            elif "mode" in p:
                self.state["thermostat"]["mode"] = p["mode"]
            return action.reply
        if kind == "fan":
            self.home.set_fan(p["speed"])
            return action.reply
        if kind == "door":
            if not p["locked"] and p.get("pin") != self.pin:
                return "I can't unlock the front door without the correct PIN."
            self.home.set_door_locked(p["locked"])
            return action.reply
        if kind == "blinds":
            self.home.set_blinds(p["room"], p["open_pct"])
            return action.reply
        if kind == "scene":
            for step in scene_actions(p["scene"]):
                self.execute(Action(step["kind"], step["params"]), heard=heard)
            return action.reply
        if kind == "status":
            return self.home.summary()
        if kind == "energy":
            e = self.home.energy_watts()
            return (
                f"Right now the house uses {e['total']} watts: "
                f"{e['lights']} for lights, {e['thermostat']} for the thermostat, "
                f"{e['fan']} for the fan."
            )
        if kind == "timer":
            inner: Action = p["action"]
            self.timers.append(Timer(self.clock_s + p["delay_s"], inner, inner.reply))
            return action.reply
        return action.reply  # unknown

    # -- virtual clock --------------------------------------------------
    def tick(self, seconds: float) -> list[str]:
        """Advance the clock and fire any due timers. Returns their replies."""
        self.clock_s += seconds
        fired = []
        due, self.timers = [t for t in self.timers if t.due_s <= self.clock_s], [
            t for t in self.timers if t.due_s > self.clock_s
        ]
        for timer in due:
            reply = self.execute(timer.action)
            fired.append(reply)
            self.audit.append(AuditEntry(self.clock_s, f"[timer] {timer.label}", reply))
        return fired

    def pending_timers(self) -> list[str]:
        return [
            f"{t.label} in {max(0, int(t.due_s - self.clock_s))}s" for t in self.timers
        ]
