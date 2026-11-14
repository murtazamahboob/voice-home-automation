"""Tests for the agent: scenes, PIN safety, timers, audit, determinism."""
import numpy as np

from homevoice.agent import VoiceHomeAgent
from homevoice.audio import generate_wake_word


def test_wake_word_arms_agent():
    agent = VoiceHomeAgent()
    assert agent.hear_audio(generate_wake_word()) is True
    assert agent.awake is True
    assert agent.hear_audio(np.zeros(7200, dtype=np.float32)) is False


def test_command_turns_light_on():
    agent = VoiceHomeAgent()
    reply = agent.handle_command("turn on the kitchen light")
    assert "kitchen" in reply
    assert agent.home.state["lights"]["kitchen"]["on"] is True


def test_unlock_without_pin_refused():
    agent = VoiceHomeAgent()
    agent.handle_command("unlock the front door pin 1234")
    reply = agent.handle_command("lock the front door")
    assert agent.home.state["door"]["locked"] is True
    reply = agent.handle_command("unlock the front door")
    assert "PIN" in reply
    assert agent.home.state["door"]["locked"] is True


def test_unlock_with_wrong_pin_refused():
    agent = VoiceHomeAgent()
    reply = agent.handle_command("unlock the front door pin 9999")
    assert "PIN" in reply
    assert agent.home.state["door"]["locked"] is True


def test_unlock_with_correct_pin():
    agent = VoiceHomeAgent()
    reply = agent.handle_command("unlock the front door pin 1234")
    assert agent.home.state["door"]["locked"] is False


def test_good_night_scene():
    agent = VoiceHomeAgent()
    agent.handle_command("turn on the kitchen light")
    agent.handle_command("set the thermostat to 25 degrees")
    agent.handle_command("good night")
    assert all(not l["on"] for l in agent.home.state["lights"].values())
    assert agent.home.state["door"]["locked"] is True
    assert agent.home.state["thermostat"]["target_c"] == 19.0
    assert agent.home.state["blinds"]["living room"]["open_pct"] == 0


def test_movie_night_scene():
    agent = VoiceHomeAgent()
    agent.handle_command("movie night")
    assert agent.home.state["lights"]["living room"]["brightness"] == 20
    assert agent.home.state["lights"]["living room"]["on"] is True
    assert agent.home.state["lights"]["kitchen"]["on"] is False


def test_timer_fires_after_tick():
    agent = VoiceHomeAgent()
    agent.handle_command("turn on the bedroom light")
    agent.handle_command("turn off the bedroom light in 5 minutes")
    assert agent.home.state["lights"]["bedroom"]["on"] is True
    assert agent.tick(4 * 60) == []  # not yet
    assert agent.home.state["lights"]["bedroom"]["on"] is True
    fired = agent.tick(60)
    assert len(fired) == 1
    assert agent.home.state["lights"]["bedroom"]["on"] is False


def test_unknown_command_changes_nothing():
    agent = VoiceHomeAgent()
    before = agent.home.snapshot()
    reply = agent.handle_command("order me a pizza")
    assert "didn't understand" in reply
    assert agent.home.snapshot() == before


def test_audit_log_records_every_command():
    agent = VoiceHomeAgent()
    agent.handle_command("turn on the kitchen light")
    agent.handle_command("set the thermostat to 22 degrees")
    assert len(agent.audit) == 2
    assert agent.audit[0].heard == "turn on the kitchen light"


def test_energy_reply_reports_watts():
    agent = VoiceHomeAgent()
    agent.handle_command("turn on the kitchen light")
    reply = agent.handle_command("how much energy is the house using")
    assert "9.0 watts" in reply


def test_demo_session_is_deterministic():
    def run():
        agent = VoiceHomeAgent()
        agent.hear_audio(generate_wake_word())
        for text in (
            "turn on the living room light",
            "set the thermostat to 22 degrees",
            "movie night",
        ):
            agent.handle_command(text)
        return agent.home.snapshot()

    assert run() == run()
