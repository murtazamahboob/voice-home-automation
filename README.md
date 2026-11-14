# Voice-Controlled Home Automation Agent

A **voice-controlled home automation agent** — say "hey home", then tell the house what to do: lights, thermostat, fan, door lock, blinds, named scenes, timers and a live energy report. Fully offline: a three-note wake-word chime, a forgiving command parser and a simulated house, with no microphone, no network and no API key.

**Verified result (deterministic, reproduced in a fresh venv): 49/49 tests pass. Demo: wake word detected, 9 commands run, PIN-less unlock refused, timer fires after 5 minutes, final draw 881.8 W.**

## Why this project is different

- **It has a safety rule, not just a parser.** Unlocking the front door by voice needs the spoken PIN — a missing or wrong PIN is a refusal, never a guess. That one rule is what makes a voice-controlled lock shippable instead of a demo hazard.
- **It wakes up first.** A three-note chime (660 / 880 / 660 Hz) is the wake word, detected by FFT peak-picking on each note window — so the listen → wake → command loop is real and testable end to end.
- **One phrase runs the whole house.** "Good night" turns every light off, locks the door, drops the thermostat to 19 C, closes the blinds and stops the fan. "Movie night", "good morning" and "away" are built the same way, from the same actions single commands use.
- **Timers run on a virtual clock.** "Turn off the bedroom light in 5 minutes" schedules the action and fires it when the clock advances — testable in milliseconds, with an audit log of everything the agent heard and did.

## Demo result

| Step | Command | Result |
|---|---:|---|
| 1 | wake-word chime | detected |
| 2 | turn on the living room light | on, 100% |
| 3 | set the living room light to 30 percent | 30% |
| 4 | set the thermostat to 22 degrees | 22 C, heat |
| 5 | turn the fan to medium | medium |
| 6 | unlock the front door (no PIN) | refused — PIN required |
| 7 | unlock the front door pin 1234 | unlocked |
| 8 | movie night | living room 20%, blinds closed |
| 9 | turn off the kitchen light in 5 minutes | scheduled, fires on tick |
| 10 | how much energy is the house using | 881.8 W total |

## Installation

```bash
git clone https://github.com/murtazamahboob/voice-home-automation.git
cd voice-home-automation
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Full demo: wake word + 9 commands + timer + energy report
python examples/demo.py
# -> outputs/session.md, outputs/wake_word.wav

# One command at a time
homevoice command "turn on the kitchen light"
homevoice command "unlock the front door pin 1234"
homevoice command "good night"

# House status and energy use
homevoice status

# Wake-word check (writes the chime to outputs/wake_word.wav)
homevoice listen
```

## Example output

```
wake word detected: True
> hey home, turn on the living room light
  Turning on the living room light.
> unlock the front door
  I can't unlock the front door without the correct PIN.
> movie night
  Setting the movie night scene.
[timer] Turning off the kitchen light.
Lights: living room (20%). Thermostat: 22.0 C, heat. Fan: medium. Front door: unlocked. Blinds: living room 0% open, bedroom 100% open.
energy: {'lights': 1.8, 'thermostat': 800.0, 'fan': 80.0, 'total': 881.8}
session=outputs/session.md
```

## How it works

```
audio ──▶ wake-word detector (FFT, 3 notes in order) ──▶ awake
                                                          │
text command ──▶ parser (room, device, value, PIN) ──▶ action
                                                          │
                                              home state + scenes + timers
                                                          │
                                              spoken reply + audit log
```

- **Audio** (`src/homevoice/audio.py`): wake-word chime synthesis + FFT detection, WAV writer.
- **Commands** (`src/homevoice/commands.py`): forgiving natural-language parser, PIN-gated door.
- **Devices** (`src/homevoice/devices.py`): simulated house — 4 rooms of lights, thermostat (16–30 C), fan, door lock, blinds, energy model.
- **Scenes** (`src/homevoice/scenes.py`): good night, movie night, good morning, away, all off.
- **Agent** (`src/homevoice/agent.py`): listen → wake → command loop, virtual clock timers, audit log.
- **CLI** (`src/homevoice/cli.py`): `homevoice demo` / `command` / `status` / `listen`.

## Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -q
# 49 passed
```

Tests cover wake-word detection (right notes, wrong notes, wrong order, silence, too quiet, too short), the parser (phrasing variants, brightness, thermostat, fan, blinds, scenes, timers, unknown input), device clamping and energy math, PIN safety, scenes, timer firing, the audit log and demo determinism.

## Project structure

```
voice-home-automation/
├── src/homevoice/    # audio.py, commands.py, devices.py, scenes.py, agent.py, cli.py
├── tests/            # test_audio.py, test_commands.py, test_devices.py, test_agent.py (49 tests)
├── examples/         # demo.py (scripted session + report)
├── outputs/          # session.md, wake_word.wav (generated, not committed)
├── README.md
├── LICENSE
├── pyproject.toml
└── requirements.txt
```

## License

MIT — see [LICENSE](LICENSE).
