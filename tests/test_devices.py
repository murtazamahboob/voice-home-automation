"""Tests for the simulated home state."""
from homevoice.devices import HomeState


def test_default_state_is_safe():
    home = HomeState()
    assert all(not l["on"] for l in home.state["lights"].values())
    assert home.state["door"]["locked"] is True
    assert home.state["thermostat"]["target_c"] == 22.0
    assert home.state["fan"]["speed"] == 0


def test_light_on_and_brightness_clamped():
    home = HomeState()
    home.set_light("kitchen", True, 250)
    assert home.state["lights"]["kitchen"]["brightness"] == 100
    home.set_light("kitchen", True, -5)
    assert home.state["lights"]["kitchen"]["brightness"] == 0


def test_light_all_rooms():
    home = HomeState()
    home.set_light("all", True)
    assert all(l["on"] for l in home.state["lights"].values())


def test_dim_turns_light_off_at_zero():
    home = HomeState()
    home.set_light("bedroom", True, 10)
    home.dim_light("bedroom", -20)
    assert home.state["lights"]["bedroom"]["brightness"] == 0
    assert home.state["lights"]["bedroom"]["on"] is False


def test_thermostat_clamped():
    home = HomeState()
    home.set_thermostat(40.0)
    assert home.state["thermostat"]["target_c"] == 30.0
    home.set_thermostat(5.0)
    assert home.state["thermostat"]["target_c"] == 16.0


def test_thermostat_adjust():
    home = HomeState()
    home.adjust_thermostat(2)
    assert home.state["thermostat"]["target_c"] == 24.0


def test_fan_speed_clamped():
    home = HomeState()
    home.set_fan(9)
    assert home.state["fan"]["speed"] == 3


def test_blinds_clamped():
    home = HomeState()
    home.set_blinds("bedroom", 150)
    assert home.state["blinds"]["bedroom"]["open_pct"] == 100


def test_energy_zero_at_rest():
    home = HomeState()
    assert home.energy_watts()["total"] == 0.0


def test_energy_counts_lights_and_thermostat():
    home = HomeState()
    home.set_light("kitchen", True, 100)
    home.set_thermostat(24.0)
    e = home.energy_watts()
    assert e["lights"] == 9.0
    assert e["thermostat"] == 800.0
    assert e["total"] == 809.0


def test_summary_mentions_state():
    home = HomeState()
    home.set_light("kitchen", True, 50)
    summary = home.summary()
    assert "kitchen (50%)" in summary
    assert "locked" in summary
