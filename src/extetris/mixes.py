"""Piece mixes: which pieces appear, and how often.

This replaces the starter's trick of repeating an index in a list to make a
piece more likely (allextetrominoes.get_any_extetromino). That trick worked
on index numbers, and because the starter's list itself repeats some shapes
(docs/analysis.md §1), the numbers a designer wrote were not the chances
players actually got.

Functional-OO design
--------------------
A PieceMix is an object wrapping one *function*:

    weight(piece_info, lines_cleared) -> a number >= 0

Everything else is built by making new weight functions out of old ones:

    mix(...)          A: weights the designer writes down
    only(...)         A: equal weights for a chosen set of pieces
    MODES[...]        B: ready-made mixes (classic, easy, normal, hard, chaos)
    progressive(...)  C: a mix that changes as more lines are cleared

Examples
--------
    mix(NoHole=60, OneHole=30, TwoHole=10)   # 60 % of pieces are NoHole, ...
    mix({"I": 3, "O": 1})                    # I three times as likely as O
    mix(classic=80, TwoHole=20)              # "classic" = the 7 normal pieces
    only("I", "O", "T")
    progressive(["classic", "easy", "normal", "hard"], every_lines=10)
"""
from collections import defaultdict

from .pieces import DIFFICULTY_CLASSES, ExTetromino

CLASSIC_NAMES = ("I", "O", "T", "S", "Z", "L", "Γ")


def _all_pieces():
    return ExTetromino.catalogue()


def _group(key):
    """The pieces a mix key refers to: a group, class or piece name."""
    if isinstance(key, type):
        key = key.__name__
    if key == "classic":
        return [i for i in _all_pieces() if i.name in CLASSIC_NAMES]
    if key == "all":
        return list(_all_pieces())
    for cls in DIFFICULTY_CLASSES:
        if key == cls.__name__:
            return list(cls.catalogue())
    info = ExTetromino._find(key)
    if info is not None:
        return [info]
    raise ValueError(
        f"unknown piece or group {key!r}; use a piece name (e.g. 'T', "
        f"'TwoHole-03'), a class name (e.g. 'TwoHole'), 'classic' or 'all'")


class PieceMix:
    """How likely each piece is, possibly depending on lines cleared."""

    def __init__(self, weight, name="custom"):
        """weight: function (PieceInfo, lines_cleared) -> number >= 0."""
        self.weight = weight
        self.name = name

    def probabilities(self, lines=0):
        """{piece name: chance} for a game with `lines` lines cleared."""
        raw = {i.name: float(self.weight(i, lines)) for i in _all_pieces()}
        bad = [n for n, w in raw.items() if w < 0]
        if bad:
            raise ValueError(f"negative weight for {bad}")
        total = sum(raw.values())
        if total <= 0:
            raise ValueError(f"mix {self.name!r} gives no pieces at {lines} lines")
        return {n: w / total for n, w in raw.items() if w > 0}

    def probabilities_by_class(self, lines=0):
        """{class name: chance} - handy for checking a mix."""
        by_class = defaultdict(float)
        probs = self.probabilities(lines)
        for info in _all_pieces():
            if info.name in probs:
                by_class[info.piece_class.__name__] += probs[info.name]
        return dict(by_class)

    def expected_holes(self, lines=0):
        """Average spawn holes per piece: a rough difficulty score."""
        probs = self.probabilities(lines)
        return sum(p * ExTetromino._find(n).spawn_holes for n, p in probs.items())

    def draw(self, rng, lines=0):
        """A new piece, chosen with these chances."""
        probs = self.probabilities(lines)
        names = list(probs)
        name = rng.choices(names, weights=[probs[n] for n in names])[0]
        info = ExTetromino._find(name)
        return info.piece_class(info.name, rng=rng)

    def __call__(self, rng, lines=0):
        return self.draw(rng, lines)

    def __repr__(self):
        return f"PieceMix({self.name!r})"


# --- A: mixes a designer writes down ---------------------------------------------
def mix(weights=None, name="custom", **more):
    """A mix from weights for groups of pieces.

    Keys can be a piece name ("T", "TwoHole-03"), a class name ("TwoHole"),
    "classic" (the 7 normal pieces) or "all". A group's weight is shared
    equally among its pieces, so NoHole=60 means 60 % of all pieces are
    NoHole ones. If groups overlap, a piece gets the sum of its shares.
    Names that aren't valid Python keywords go in a dict: mix({"Γ": 2}).
    """
    table = dict(weights or {})
    table.update(more)
    if not table:
        raise ValueError("give at least one weight")
    per_piece = defaultdict(float)
    for key, w in table.items():
        if w < 0:
            raise ValueError(f"weight for {key!r} is negative")
        group = _group(key)
        for info in group:
            per_piece[info.name] += w / len(group)
    if sum(per_piece.values()) <= 0:
        raise ValueError("all weights are zero")
    frozen = dict(per_piece)
    return PieceMix(lambda info, lines: frozen.get(info.name, 0.0), name)


def only(*keys, name="custom"):
    """Every chosen piece equally likely, e.g. only("I", "O", "T")."""
    names = {i.name for k in keys for i in _group(k)}
    return mix({n: 1 for n in names}, name=name)


# --- B: ready-made modes ---------------------------------------------------------
MODES = {
    "classic": only("classic", name="classic"),
    "easy": mix(classic=85, OneHole=15, name="easy"),
    "normal": mix(classic=55, OneHole=20, TwoHole=15, ThreeHole=5,
                  FourHole=4, SixHole=1, name="normal"),
    "hard": mix(classic=25, OneHole=25, TwoHole=25, ThreeHole=12,
                FourHole=10, SixHole=3, name="hard"),
    "chaos": only("all", name="chaos"),
}


def mode(name_or_mix):
    """A PieceMix from a mode name ('easy', 'progressive', ...) or a mix."""
    if isinstance(name_or_mix, PieceMix):
        return name_or_mix
    if name_or_mix == "progressive":
        return progressive()
    try:
        return MODES[name_or_mix]
    except KeyError:
        raise ValueError(f"unknown mode {name_or_mix!r}; choose from "
                         f"{', '.join(list(MODES) + ['progressive'])}") from None


# --- C: a mix that changes during the game ---------------------------------------
def progressive(stages=("classic", "easy", "normal", "hard"), every_lines=10,
                name="progressive"):
    """Use stages[0] at first, then move to the next stage every
    `every_lines` lines cleared, staying on the last one.

    With the defaults: classic pieces only until 10 lines, then easy, then
    normal at 20 lines, and hard from 30 lines on.
    """
    if every_lines < 1:
        raise ValueError("every_lines must be at least 1")
    mixes = [mode(s) for s in stages]
    if not mixes:
        raise ValueError("give at least one stage")

    def stage(lines):
        return mixes[min(lines // every_lines, len(mixes) - 1)]

    return PieceMix(lambda info, lines: stage(lines).weight(info, lines), name)
