"""Command-line interface for the voice home agent."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from homevoice.agent import VoiceHomeAgent
from homevoice.audio import generate_wake_word, write_wav

# Scripted demo session: every command is fixed, so the demo is deterministic.
DEMO_COMMANDS = [
    "hey home, turn on the living room light",
    "set the living room light to 30 percent",
    "set the thermostat to 22 degrees",
    "turn the fan to medium",
    "unlock the front door",  # no PIN — must be refused
    "unlock the front door pin 1234",
    "movie night",
    "turn off the kitchen light in 5 minutes",
    "how much energy is the house using",
]


def _demo(out_path: str = "outputs/session.md") -> int:
    agent = VoiceHomeAgent()
    lines = ["# Voice Home Automation — demo session", ""]
    heard = agent.hear_audio(generate_wake_word())
    lines.append(f"Wake word heard: {heard}")
    print(f"wake word detected: {heard}")
    root = Path(__file__).resolve().parents[2]
    outdir = root / "outputs"
    outdir.mkdir(exist_ok=True)
    write_wav(str(outdir / "wake_word.wav"), generate_wake_word())
    for text in DEMO_COMMANDS:
        reply = agent.handle_command(text)
        lines.append(f"- You: {text}")
        lines.append(f"- Home: {reply}")
        print(f"> {text}\n  {reply}")
    fired = agent.tick(5 * 60)
    for reply in fired:
        lines.append(f"- [timer fired after 5 min] Home: {reply}")
        print(f"[timer] {reply}")
    lines.append("")
    lines.append(f"Final state: {agent.home.summary()}")
    energy = agent.home.energy_watts()
    lines.append(f"Energy: {energy['total']} W total "
                 f"(lights {energy['lights']}, thermostat {energy['thermostat']}, fan {energy['fan']})")
    lines.append(f"Audit entries: {len(agent.audit)}")
    print(agent.home.summary())
    print(f"energy: {energy}")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"session={out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="homevoice", description="Voice-controlled home automation (offline demo).")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="run the scripted demo session")
    demo.add_argument("--out", default="outputs/session.md")

    cmd = sub.add_parser("command", help="run one spoken command")
    cmd.add_argument("text", help='e.g. "turn on the kitchen light"')
    cmd.add_argument("--pin", default="1234", help="door PIN (default 1234)")

    sub.add_parser("status", help="print the house status")
    sub.add_parser("listen", help="generate the wake-word chime and check detection")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        return _demo(args.out)
    agent = VoiceHomeAgent(pin=getattr(args, "pin", "1234"))
    if args.command == "listen":
        samples = generate_wake_word()
        write_wav("outputs/wake_word.wav", samples)
        print(f"wake word detected: {agent.hear_audio(samples)}")
        print("wrote outputs/wake_word.wav")
        return 0
    if args.command == "status":
        print(agent.home.summary())
        print(json.dumps(agent.home.energy_watts()))
        return 0
    if args.command == "command":
        print(agent.handle_command(args.text))
        print(agent.home.summary())
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
