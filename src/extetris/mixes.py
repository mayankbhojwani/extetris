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
    assistive(...),   D: a mix that looks at the board before choosing
    unfair(...)          (6 Nov tutorial: fair, assistive and unfair games)

Examples
--------
    mix(NoHole=60, OneHole=30, TwoHole=10)   # 60 % of pieces are NoHole, ...
    mix({"I": 3, "O": 1})                    # I three times as likely as O
    mix(classic=80, TwoHole=20)              # "classic" = the 7 normal pieces
    only("I", "O", "T")
    progressive(["classic", "easy", "normal", "hard"], every_lines=10)
    mix({"box:3x3": 50, "classic": 50})      # pieces chosen by bounding box
    assistive("normal", strength=0.7)        # prefers pieces that fit the board
    unfair("classic")                        # prefers pieces that don't fit

Groups a mix key can name
-------------------------
    "T", "TwoHole-03"   one piece
    "TwoHole"           a difficulty class (holes of the spawn turn)
    "classic", "all"    the 7 normal pieces / all 34
    "box:3x3"           pieces whose bounding box is 3 by 3 (or "4x2", ...)
    "guaranteed:2"      pieces sure to leave 2 holes however they are turned
    "deepest:2"         pieces whose deepest one-column hole is 2 squares
    "fill>=50"          pieces filling at least 50 % of their bounding box
"""
import re
from collections import defaultdict

from . import geometry as g
from .pieces import DIFFICULTY_CLASSES, ExTetromino

CLASSIC_NAMES = ("I", "O", "T", "S", "Z", "L", "Γ")


def _all_pieces():
    return ExTetromino.catalogue()


# "property groups": select pieces by a measured property, not by name.
_PROPERTY_GROUPS = (
    (re.compile(r"box:(\d+)x(\d+)$"),
     lambda i, m: i.box_size == f"{max(m)}x{min(m)}"),
    (re.compile(r"guaranteed:(\d+)$"), lambda i, m: i.guaranteed_holes == m[0]),
    (re.compile(r"deepest:(\d+)$"), lambda i, m: i.deepest_hole == m[0]),
    (re.compile(r"fill>=(\d+)$"), lambda i, m: i.box_fill * 100 >= m[0] - 1e-9),
)


def property_groups():
    """Every property group that holds at least one piece, e.g. 'box:3x3'
    (for menus such as the designer's)."""
    infos = _all_pieces()
    keys = sorted({f"box:{i.box_size}" for i in infos})
    keys += [f"guaranteed:{n}" for n in sorted({i.guaranteed_holes for i in infos})]
    keys += [f"deepest:{n}" for n in sorted({i.deepest_hole for i in infos})]
    keys += [f"fill>={p}" for p in (25, 33, 44, 50, 66, 100)]
    return keys


def _group(key):
    """The pieces a mix key refers to: a piece, class, group or property group."""
    if isinstance(key, type):
        key = key.__name__
    if not isinstance(key, str):
        raise ValueError(f"unknown piece or group {key!r}")
    for pattern, test in _PROPERTY_GROUPS:
        found = pattern.match(key)
        if found:
            numbers = tuple(int(x) for x in found.groups())
            group = [i for i in _all_pieces() if test(i, numbers)]
            if not group:
                raise ValueError(f"no piece is in the group {key!r}")
            return group
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
        f"'TwoHole-03'), a class name (e.g. 'TwoHole'), 'classic', 'all', or a "
        f"property group such as 'box:3x3', 'guaranteed:2', 'deepest:1', 'fill>=50'")


class PieceMix:
    """How likely each piece is, possibly depending on lines cleared."""

    def __init__(self, weight, name="custom"):
        """weight: function (PieceInfo, lines_cleared) -> number >= 0."""
        self.weight = weight
        self.name = name

    def probabilities(self, lines=0, board=None):
        """{piece name: chance} for a game with `lines` lines cleared.
        A plain mix ignores `board`; BoardAwareMix uses it."""
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

    def draw(self, rng, lines=0, board=None):
        """A new piece, chosen with these chances."""
        probs = self.probabilities(lines, board)
        names = list(probs)
        name = rng.choices(names, weights=[probs[n] for n in names])[0]
        info = ExTetromino._find(name)
        return info.piece_class(info.name, rng=rng)

    def __call__(self, rng, lines=0, board=None):
        return self.draw(rng, lines, board)

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


# --- D: a mix that looks at the board ----------------------------------------------
#
# 6 Nov tutorial: a game can be "fair" (pieces come regardless of what is on the
# ground), "unfair" (the next piece is one that won't fit the holes, so lines pile
# up) or "assistive" (the next piece always has a place where it fills part of a
# line without leaving a hole). Plain mixes above can only be fair, because they
# see nothing but a random number and the lines cleared. A BoardAwareMix also
# gets the board.

STYLES = ("fair", "assistive", "unfair")
_TURNS = {}


def _turns(info):
    if info.name not in _TURNS:
        _TURNS[info.name] = g.distinct_rotations(info.standard_turn)
    return _TURNS[info.name]


def new_holes(board, info):
    """The fewest new holes this piece can leave on `board`, trying every turn
    and column and dropping it straight down (rows it fills are cleared first,
    so filling a line counts in its favour). None if it fits nowhere."""
    before = board.holes()
    best = None
    for turn in _turns(info):
        for col in range(board.width - turn.shape[1] + 1):
            row = board.drop_row(turn, col)
            if row is None:
                continue
            after, _ = board.place(turn, row, col).clear_full_rows()
            added = after.holes() - before
            if best is None or added < best:
                best = added
    return best


class BoardAwareMix(PieceMix):
    """A mix that changes its chances to suit the board, in one of STYLES.

    base:      the mix it starts from (a mode name or any PieceMix).
    style:     "assistive" favours the pieces that leave the fewest new holes,
               "unfair" the ones that leave the most (a piece that fits nowhere
               counts as the worst), "fair" ignores the board.
    strength:  0 to 1. At 1 only the favoured pieces can come; at 0.5 the
               others keep half their chance; 0 is the same as "fair".

    The next piece is chosen when the one before it appears (so the preview can
    show it), so it is judged on the board as it is at that moment.
    """

    def __init__(self, base="classic", style="assistive", strength=1.0, name=None):
        if style not in STYLES:
            raise ValueError(f"style must be one of {', '.join(STYLES)}, not {style!r}")
        if isinstance(strength, bool) or not isinstance(strength, (int, float)) \
                or not 0 <= strength <= 1:
            raise ValueError("strength must be a number from 0 to 1")
        self.base = mode(base)
        self.style = style
        self.strength = float(strength)
        super().__init__(self.base.weight, name or f"{style} {self.base.name}")

    def probabilities(self, lines=0, board=None):
        probs = self.base.probabilities(lines)
        if board is None or self.style == "fair" or self.strength == 0:
            return probs
        worst = board.width * board.height        # "fits nowhere"
        fit = {}
        for n in probs:
            added = new_holes(board, ExTetromino._find(n))
            fit[n] = worst if added is None else added
        pick = min if self.style == "assistive" else max
        target = pick(fit.values())
        s = self.strength
        raw = {n: p * ((1 - s) + s * (fit[n] == target)) for n, p in probs.items()}
        total = sum(raw.values())
        return {n: w / total for n, w in raw.items() if w > 0}

    def __repr__(self):
        return f"BoardAwareMix({self.base.name!r}, {self.style!r}, {self.strength})"


def fair(base="classic"):
    """Chances never depend on the board (any plain mix already behaves so)."""
    return BoardAwareMix(base, "fair", 0)


def assistive(base="classic", strength=1.0):
    """Prefer pieces that have a place leaving no new holes."""
    return BoardAwareMix(base, "assistive", strength)


def unfair(base="classic", strength=1.0):
    """Prefer pieces that can't be placed without leaving holes."""
    return BoardAwareMix(base, "unfair", strength)
