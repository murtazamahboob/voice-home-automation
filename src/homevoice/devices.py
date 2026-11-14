"""Simulated smart home: devices, state, and energy use.

Everything is a plain in-memory model — no real hardware, no network. The
model is deliberately strict: brightness and temperature are clamped to safe
ranges, and the front door can only be unlocked with the PIN, so the voice
layer above it cannot put the house in an unsafe state by mishearing a
command.
"""
from __future__ import annotations

from copy import deepcopy

ROOMS = ("living room", "bedroom", "kitchen", "bathroom")

LIGHT_WATTS = 9.0       # per light, at full brightness
THERMOSTAT_WATTS = 800.0
FAN_WATTS_PER_SPEED = 40.0
BLINDS_WATTS = 0.0      # blinds draw nothing once positioned

MIN_TEMP_C = 16.0
MAX_TEMP_C = 30.0
DEFAULT_TEMP_C = 22.0


def default_state() -> dict:
    """The house at rest: lights off, 22 C, fan off, door locked."""
    return {
        "lights": {room: {"on": False, "brightness": 100} for room in ROOMS},
        "thermostat": {"target_c": DEFAULT_TEMP_C, "mode": "off"},
        "fan": {"speed": 0},  # 0 off, 1 low, 2 medium, 3 high
        "door": {"locked": True},
        "blinds": {room: {"open_pct": 100} for room in ("living room", "bedroom")},
    }


class HomeState:
    """Holds the device state and applies parsed actions to it."""

    def __init__(self, state: dict | None = None):
        self.state = deepcopy(state) if state is not None else default_state()

    def snapshot(self) -> dict:
        return deepcopy(self.state)

    # -- lights ---------------------------------------------------------
    def set_light(self, room: str, on: bool, brightness: int | None = None) -> None:
        if room == "all":
            for r in ROOMS:
                self.set_light(r, on, brightness)
            return
        light = self.state["lights"][room]
        light["on"] = on
        if brightness is not None:
            light["brightness"] = max(0, min(100, int(brightness)))
        elif on and light["brightness"] == 0:
            light["brightness"] = 100

    def dim_light(self, room: str, delta: int) -> None:
        rooms = ROOMS if room == "all" else (room,)
        for r in rooms:
            light = self.state["lights"][r]
            light["brightness"] = max(0, min(100, light["brightness"] + delta))
            light["on"] = light["brightness"] > 0

    # -- climate --------------------------------------------------------
    def set_thermostat(self, temp_c: float, mode: str | None = None) -> None:
        temp_c = max(MIN_TEMP_C, min(MAX_TEMP_C, float(temp_c)))
        self.state["thermostat"]["target_c"] = temp_c
        if mode:
            self.state["thermostat"]["mode"] = mode
        elif self.state["thermostat"]["mode"] == "off":
            self.state["thermostat"]["mode"] = "heat" if temp_c >= 20 else "heat"

    def adjust_thermostat(self, delta: float) -> None:
        self.set_thermostat(self.state["thermostat"]["target_c"] + delta)

    def set_fan(self, speed: int) -> None:
        self.state["fan"]["speed"] = max(0, min(3, int(speed)))

    # -- door & blinds --------------------------------------------------
    def set_door_locked(self, locked: bool) -> None:
        self.state["door"]["locked"] = locked

    def set_blinds(self, room: str, open_pct: int) -> None:
        rooms = ("living room", "bedroom") if room == "all" else (room,)
        for r in rooms:
            if r in self.state["blinds"]:
                self.state["blinds"][r]["open_pct"] = max(0, min(100, int(open_pct)))

    # -- energy & summary ----------------------------------------------
    def energy_watts(self) -> dict:
        """Instantaneous draw, broken down by device class."""
        lights = sum(
            LIGHT_WATTS * (light["brightness"] / 100.0)
            for light in self.state["lights"].values()
            if light["on"]
        )
        thermostat = (
            THERMOSTAT_WATTS if self.state["thermostat"]["mode"] != "off" else 0.0
        )
        fan = FAN_WATTS_PER_SPEED * self.state["fan"]["speed"]
        total = lights + thermostat + fan
        return {
            "lights": round(lights, 1),
            "thermostat": round(thermostat, 1),
            "fan": round(fan, 1),
            "total": round(total, 1),
        }

    def summary(self) -> str:
        lights_on = [
            f"{room} ({light['brightness']}%)"
            for room, light in self.state["lights"].items()
            if light["on"]
        ]
        lights = ", ".join(lights_on) if lights_on else "all off"
        thermo = self.state["thermostat"]
        fan_names = ("off", "low", "medium", "high")
        door = "locked" if self.state["door"]["locked"] else "unlocked"
        blinds = ", ".join(
            f"{room} {b['open_pct']}% open" for room, b in self.state["blinds"].items()
        )
        return (
            f"Lights: {lights}. Thermostat: {thermo['target_c']} C, {thermo['mode']}. "
            f"Fan: {fan_names[self.state['fan']['speed']]}. "
            f"Front door: {door}. Blinds: {blinds}."
        )
