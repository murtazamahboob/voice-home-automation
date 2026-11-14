"""Tests for the command parser."""
from homevoice.commands import parse


def test_light_on_with_room():
    a = parse("turn on the kitchen light")
    assert a.kind == "light" and a.params["room"] == "kitchen" and a.params["on"] is True


def test_light_off_phrasing_variant():
    a = parse("lights off in the bedroom")
    assert a.kind == "light" and a.params["room"] == "bedroom" and a.params["on"] is False


def test_light_brightness_percent():
    a = parse("set the living room light to 30 percent")
    assert a.kind == "light" and a.params["brightness"] == 30 and a.params["on"] is True


def test_light_dim():
    a = parse("dim the bedroom light by 20")
    assert a.kind == "light" and a.params["delta"] == -20


def test_light_defaults_to_all_rooms():
    a = parse("turn on the lights")
    assert a.kind == "light" and a.params["room"] == "all"


def test_thermostat_set():
    a = parse("set the thermostat to 22 degrees")
    assert a.kind == "thermostat" and a.params["target_c"] == 22.0


def test_thermostat_raise():
    a = parse("raise the temperature by 2 degrees")
    assert a.kind == "thermostat" and a.params["delta"] == 2.0


def test_fan_speed():
    a = parse("turn the fan to high")
    assert a.kind == "fan" and a.params["speed"] == 3


def test_door_unlock_needs_pin():
    a = parse("unlock the front door")
    assert a.kind == "door" and a.params["locked"] is False and a.params["pin"] is None


def test_door_unlock_with_pin():
    a = parse("unlock the front door pin 1234")
    assert a.kind == "door" and a.params["pin"] == "1234"


def test_door_lock():
    a = parse("lock the front door")
    assert a.kind == "door" and a.params["locked"] is True


def test_blinds_close():
    a = parse("close the living room blinds")
    assert a.kind == "blinds" and a.params["open_pct"] == 0


def test_scene_good_night():
    a = parse("hey home, good night")
    assert a.kind == "scene" and a.params["scene"] == "good night"


def test_wake_word_stripped():
    a = parse("hey home, turn on the kitchen light")
    assert a.kind == "light" and a.params["room"] == "kitchen"


def test_timer_parses_inner_action():
    a = parse("turn off the bedroom light in 5 minutes")
    assert a.kind == "timer" and a.params["delay_s"] == 300
    assert a.params["action"].kind == "light"


def test_status_and_energy():
    assert parse("what is the house status").kind == "status"
    assert parse("how much energy is the house using").kind == "energy"


def test_unknown_command():
    a = parse("order me a pizza with extra cheese")
    assert a.kind == "unknown"
    assert "didn't understand" in a.reply


def test_empty_command():
    assert parse("   ").kind == "unknown"
