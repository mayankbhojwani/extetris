"""Variant: a whole game variant described as data, with no code.

A variant is saved as a small JSON file (".json"), which the Variant
Designer window writes for you. It holds everything about a variant: name,
board size, speed and which pieces appear. Because it is plain data, a game
designer never has to write Python.

Example file:

    {
      "format": "extetris-variant/1",
      "name": "Gentle Start",
      "author": "",
      "description": "Easy pieces first, harder ones later.",
      "board": {"width": 10, "height": 20},
      "speed": {"start_delay_ms": 1000, "speedup_every": 10,
                "speedup_factor": 0.85, "min_delay_ms": 50},
      "pieces": {"kind": "progressive", "every_lines": 5,
                 "stages": ["classic", "easy", "normal"]},
      "window": {"cell_size": 28}
    }

"pieces" can be one of:
    {"kind": "mode", "mode": "easy"}
    {"kind": "mix", "weights": {"classic": 70, "TwoHole": 30}}
    {"kind": "progressive", "every_lines": 10,
     "stages": ["classic", {"classic": 80, "OneHole": 20}, "hard"]}
A progressive stage is a mode name or a weights table like the "mix" one.
"""
import copy
import json
import random
import re
from pathlib import Path

from .game import Game
from .mixes import MODES, _group, mix, mode, progressive
from .pieces import DIFFICULTY_CLASSES, ExTetromino

FORMAT = "extetris-variant/1"
MODE_NAMES = list(MODES) + ["progressive"]
PIECE_KINDS = ("mode", "mix", "progressive")

LIMITS = {               # (smallest, largest) allowed values
    "width": (4, 40),
    "height": (4, 40),
    "start_delay_ms": (50, 5000),
    "speedup_every": (1, 1000),
    "min_delay_ms": (10, 5000),
    "cell_size": (10, 60),
}

DEFAULTS = {
    "format": FORMAT,
    "name": "My ExTetris",
    "author": "",
    "description": "",
    "board": {"width": 10, "height": 20},
    "speed": {"start_delay_ms": 1000, "speedup_every": 100,
              "speedup_factor": 0.9, "min_delay_ms": 50},
    "pieces": {"kind": "mode", "mode": "progressive"},
    "window": {"cell_size": 28},
}


def _merge(defaults, given):
    """Defaults with `given` laid on top (nested one level)."""
    out = copy.deepcopy(defaults)
    for key, value in (given or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict) and key != "pieces":
            out[key].update(value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def _is_whole(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


class Variant:
    """A game variant as data. Load, check, change, save, play or release it."""

    def __init__(self, data=None):
        """A variant from a dict (missing parts get the normal values)."""
        self.data = _merge(DEFAULTS, data)

    # --- files --------------------------------------------------------------------
    @classmethod
    def load(cls, path):
        """Read a variant file. Raises ValueError with a plain message if the
        file isn't a valid JSON variant."""
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"{Path(path).name} isn't a valid variant file "
                             f"(line {e.lineno}: {e.msg})") from None
        if not isinstance(data, dict):
            raise ValueError(f"{Path(path).name} isn't a valid variant file")
        return cls(data)

    def save(self, path):
        """Write the variant to a .json file."""
        Path(path).write_text(self.to_json(), encoding="utf-8")

    def to_json(self):
        """The variant as JSON text."""
        return json.dumps(self.data, indent=2, ensure_ascii=False) + "\n"

    # --- easy access ----------------------------------------------------------------
    @property
    def name(self):
        """The variant's name, without surrounding spaces."""
        return str(self.data.get("name", "")).strip()

    @property
    def slug(self):
        """A file-name-safe version of the name, e.g. 'gentle-start'."""
        s = re.sub(r"[^A-Za-z0-9]+", "-", self.name).strip("-").lower()
        return s or "extetris-variant"

    # --- checking -------------------------------------------------------------------
    def problems(self):
        """Everything wrong with this variant, in plain words ([] = all fine)."""
        d, out = self.data, []
        if not self.name:
            out.append("Give the variant a name.")
        for section, key in (("board", "width"), ("board", "height"),
                             ("speed", "start_delay_ms"), ("speed", "speedup_every"),
                             ("speed", "min_delay_ms"), ("window", "cell_size")):
            value = d.get(section, {}).get(key)
            lo, hi = LIMITS[key]
            if not _is_whole(value) or not lo <= value <= hi:
                out.append(f"{section} {key.replace('_', ' ')} must be a whole "
                           f"number from {lo} to {hi} (now: {value!r}).")
        f = d.get("speed", {}).get("speedup_factor")
        if not _is_number(f) or not 0 < f <= 1:
            out.append("speed speedup factor must be more than 0 and at most 1 "
                       f"(e.g. 0.9 = 10 % faster each time; now: {f!r}).")
        speed = d.get("speed", {})
        if (_is_whole(speed.get("min_delay_ms")) and _is_whole(speed.get("start_delay_ms"))
                and speed["min_delay_ms"] > speed["start_delay_ms"]):
            out.append("The fastest fall delay can't be slower than the starting one.")
        out.extend(self._piece_problems(d.get("pieces")))
        return out

    @staticmethod
    def _weights_problems(weights, where):
        if not isinstance(weights, dict) or not weights:
            return [f"{where}: give at least one group with a share."]
        out = []
        for key, w in weights.items():
            try:
                _group(key)
            except ValueError:
                out.append(f"{where}: '{key}' isn't a piece, class or group name.")
            if not _is_number(w) or w < 0:
                out.append(f"{where}: the share for '{key}' must be 0 or more.")
        if not out and sum(weights.values()) <= 0:
            out.append(f"{where}: at least one share must be more than 0.")
        return out

    def _piece_problems(self, p):
        if not isinstance(p, dict) or p.get("kind") not in PIECE_KINDS:
            return ["pieces kind must be 'mode', 'mix' or 'progressive'."]
        if p["kind"] == "mode":
            if p.get("mode") not in MODE_NAMES:
                return [f"Unknown piece mode {p.get('mode')!r}; choose from "
                        f"{', '.join(MODE_NAMES)}."]
            return []
        if p["kind"] == "mix":
            return self._weights_problems(p.get("weights"), "Piece mix")
        out = []
        every = p.get("every_lines")
        if not _is_whole(every) or every < 1:
            out.append("Gets-harder: 'every lines' must be a whole number, 1 or more.")
        stages = p.get("stages")
        if not isinstance(stages, list) or not stages:
            return out + ["Gets-harder: give at least one stage."]
        for n, stage in enumerate(stages, start=1):
            if isinstance(stage, str):
                if stage not in MODES:
                    out.append(f"Stage {n}: unknown mode {stage!r}.")
            else:
                out.extend(self._weights_problems(stage, f"Stage {n}"))
        return out

    def is_valid(self):
        """True if problems() finds nothing."""
        return not self.problems()

    def _check(self):
        problems = self.problems()
        if problems:
            raise ValueError("This variant has problems:\n- " + "\n- ".join(problems))

    # --- turning data into a game -----------------------------------------------------
    def piece_mix(self):
        """The PieceMix this variant describes."""
        self._check()
        p = self.data["pieces"]
        name = self.name
        if p["kind"] == "mode":
            return mode(p["mode"])
        if p["kind"] == "mix":
            return mix(p["weights"], name=name)
        stages = [s if isinstance(s, str) else mix(s) for s in p["stages"]]
        return progressive(stages, every_lines=p["every_lines"], name=name)

    def make_game(self, rng=None):
        """A new Game with this variant's settings."""
        self._check()
        b, s = self.data["board"], self.data["speed"]
        return Game(width=b["width"], height=b["height"],
                    pieces=self.piece_mix(), rng=rng or random.Random(),
                    start_delay_ms=s["start_delay_ms"],
                    speedup_every=s["speedup_every"],
                    speedup_factor=s["speedup_factor"],
                    min_delay_ms=s["min_delay_ms"])

    def stage_starts(self):
        """Line counts at which the piece mix changes ([0] if it never does)."""
        p = self.data["pieces"]
        if p.get("kind") == "progressive":
            return [n * p["every_lines"] for n in range(len(p["stages"]))]
        if p.get("kind") == "mode" and p.get("mode") == "progressive":
            return [0, 10, 20, 30]
        return [0]

    # --- documentation ------------------------------------------------------------------
    def describe_markdown(self):
        """A README for this variant: settings, piece chances, how to play."""
        self._check()
        d = self.data
        b, s = d["board"], d["speed"]
        lines = [f"# {self.name}", ""]
        if d.get("author"):
            lines += [f"By {d['author']}.", ""]
        if d.get("description"):
            lines += [d["description"].strip(), ""]
        pct = round((1 - s["speedup_factor"]) * 100)
        lines += [
            "## How to play", "",
            "| system | how |", "|---|---|",
            "| macOS | double-click `play.command` |",
            "| Windows | double-click `play.bat` |",
            "| Linux | `./play.sh` |", "",
            "Needs Python 3.9+ with numpy and tkinter "
            "(`python3 play.py --check` tells you what's missing).", "",
            "Keys: ← → move, ↑ turn, Z turn back, ↓ down, Space drop, P pause.", "",
            "## Settings", "",
            "| setting | value |", "|---|---|",
            f"| board | {b['width']} wide × {b['height']} tall |",
            f"| starting fall delay | {s['start_delay_ms']} ms per row |",
            f"| speed-up | {pct} % faster every {s['speedup_every']} lines "
            f"(never faster than {s['min_delay_ms']} ms) |",
            "",
            "## Pieces", "",
        ]
        m = self.piece_mix()
        for start in self.stage_starts():
            if len(self.stage_starts()) > 1:
                lines += [f"### From {start} lines cleared", ""]
            by_class = m.probabilities_by_class(start)
            lines += ["| difficulty class | chance |", "|---|---|"]
            for cls in DIFFICULTY_CLASSES:
                if cls.__name__ in by_class:
                    lines.append(f"| {cls.__name__} ({cls.SPAWN_HOLES} holes) | "
                                 f"{by_class[cls.__name__]:.0%} |")
            lines += ["", f"Average holes per piece: {m.expected_holes(start):.2f} "
                      "(classic Tetris ≈ 0.29, all 34 pieces ≈ 1.85).", ""]
            probs = m.probabilities(start)
            shown = ", ".join(f"{n} {p:.0%}" for n, p in
                              sorted(probs.items(), key=lambda kv: -kv[1]))
            lines += [f"Pieces: {shown}.", ""]
        lines += ["---", "",
                  "Made with the ExTetris Variant Designer. The variant itself "
                  "is in `variant.json`."]
        return "\n".join(lines) + "\n"


def piece_names():
    """All piece names, for menus (classics first)."""
    return [i.name for i in ExTetromino.catalogue()]
