"""ExTetromino pieces, grouped into difficulty classes by spawn holes.

Family tree:

    Shape
     └── ExTetromino          (a 4-square piece made by the generator)
          ├── NoHole          spawns leaving 0 holes   (I, O, L, T, Γ)
          ├── OneHole         spawns leaving 1 hole    (S, Z + 8 more)
          ├── TwoHole         spawns leaving 2 holes   (11 pieces)
          ├── ThreeHole       spawns leaving 3 holes   (3 pieces)
          ├── FourHole        spawns leaving 4 holes   (4 pieces)
          └── SixHole         spawns leaving 6 holes   (the long diagonal)

No piece leaves exactly 5 holes, so there is no FiveHole class.

Phase 2 decisions (see docs/ai_log/raw_log.md):
  * A piece's class = holes left by its spawn turn on a flat floor.
  * Spawn turn = flattest turn; ties go to fewer holes, then a random pick.
  * Classic pieces keep their names; the rest are named automatically
    as <Class>-<NN>, e.g. "TwoHole-03".

Usage:
    TwoHole()                 # a random two-hole piece
    TwoHole("TwoHole-03")     # a specific one, by name
    TwoHole(3)                # the 3rd piece listed by TwoHole.catalogue()
                              # (classic pieces are listed first, so OneHole(3)
                              # is "OneHole-01", after S and Z)
    ExTetromino.named("T")    # look up any piece by name -> NoHole instance
    NoHole.catalogue()        # what's in the class
"""
import random
from dataclasses import dataclass

from . import geometry as g
from .generator import PieceGenerator
from .shape import Shape

_ALIASES = {"Gamma": "Γ", "J": "Γ"}


@dataclass(frozen=True, eq=False)
class PieceInfo:
    """Everything known about one piece, independent of how it is turned."""
    name: str
    piece_class: type
    standard_turn: object   # read-only numpy array from the generator
    spawn_turns: tuple      # the turns it may appear in (random pick)
    spawn_holes: int
    box_size: str
    touching: str
    chiral: bool

    def __repr__(self):
        return (f"PieceInfo({self.name!r}, {self.piece_class.__name__}, "
                f"box={self.box_size}, touching={self.touching}, "
                f"spawn_holes={self.spawn_holes})")


def _classic_name(m):
    """Name the 7 classic tetrominoes from their properties (no stored grids)."""
    if len(g.cells(m)) != 4 or g.touching(m) != g.EDGES:
        return None
    box = g.box_size(m)
    if box == "4x1":
        return "I"
    if box == "2x2":
        return "O"
    if not g.is_chiral(m):
        return "T"
    turn = g.spawn_turns(m)[0]            # lies flat: 2 rows x 3 columns
    top, bottom = turn[0], turn[1]
    if len(g.distinct_rotations(m)) == 2:  # S or Z
        # S: top row is shifted right (·██ / ██·); Z: shifted left.
        return "S" if top.argmax() > bottom.argmax() else "Z"
    # L or Γ, lying with three squares on the floor: where's the raised square?
    return "L" if top.argmax() == 2 else "Γ"


class ExTetromino(Shape):
    """A 4-square piece. Use one of the difficulty subclasses to make one."""

    SPAWN_HOLES = None        # each difficulty class sets its own value
    GENERATOR = PieceGenerator(n_cells=4, touching=g.CORNERS)
    _catalogue_cache = None

    def __init__(self, variant=None, rng=None):
        """Make a piece of this class.

        variant: None for a random piece of this class, a name such as
                 "T" or "TwoHole-03", or its 1-based number in the class.
        rng:     an optional random.Random, so games can be replayed.
        """
        cls = type(self)
        if cls.SPAWN_HOLES is None:
            raise TypeError(
                "ExTetromino is the general family; make a piece with a "
                "difficulty class (e.g. TwoHole()) or ExTetromino.named('T')")
        rng = rng or random
        options = cls.catalogue()
        self.info = cls._choose(options, variant, rng)
        super().__init__(rng.choice(self.info.spawn_turns))

    @classmethod
    def _choose(cls, options, variant, rng):
        if variant is None:
            return rng.choice(options)
        if isinstance(variant, int) and not isinstance(variant, bool):
            if not 1 <= variant <= len(options):
                raise ValueError(f"{cls.__name__} has pieces 1..{len(options)}, "
                                 f"not {variant}")
            return options[variant - 1]
        if isinstance(variant, str):
            name = _ALIASES.get(variant, variant)
            for info in options:
                if info.name == name:
                    return info
            owner = ExTetromino._find(name)
            if owner is not None:
                right = owner.piece_class.__name__
                raise ValueError(f"{variant!r} is a {right} piece, not a "
                                 f"{cls.__name__} piece; use {right}({variant!r})")
            raise ValueError(f"no piece called {variant!r}")
        raise TypeError("variant must be None, a piece name or a number")

    # --- the catalogue ---------------------------------------------------------
    @classmethod
    def catalogue(cls):
        """PieceInfo for every piece in this class (all pieces on ExTetromino)."""
        everything = ExTetromino._build_catalogue()
        if cls is ExTetromino:
            return everything
        return tuple(i for i in everything if i.piece_class is cls)

    @staticmethod
    def _build_catalogue():
        if ExTetromino._catalogue_cache is None:
            by_holes = {c.SPAWN_HOLES: c for c in DIFFICULTY_CLASSES}
            counters = {c: 0 for c in DIFFICULTY_CLASSES}
            out = []
            for m in ExTetromino.GENERATOR.shapes():
                turns = tuple(g.spawn_turns(m))
                sh = g.holes(turns[0])
                if sh not in by_holes:
                    raise RuntimeError(f"no difficulty class for {sh} spawn holes")
                pc = by_holes[sh]
                name = _classic_name(m)
                if name is None:
                    counters[pc] += 1
                    name = f"{pc.__name__}-{counters[pc]:02d}"
                out.append(PieceInfo(name, pc, m, turns, sh, g.box_size(m),
                                     g.touching(m), g.is_chiral(m)))
            # classics first inside each class, then generator order
            order = {c: n for n, c in enumerate(DIFFICULTY_CLASSES)}
            out.sort(key=lambda i: (order[i.piece_class], "-" in i.name))
            ExTetromino._catalogue_cache = tuple(out)
        return ExTetromino._catalogue_cache

    @staticmethod
    def _find(name):
        name = _ALIASES.get(name, name)
        for info in ExTetromino._build_catalogue():
            if info.name == name:
                return info
        return None

    @staticmethod
    def named(name, rng=None):
        """Any piece by name, e.g. ExTetromino.named('T') -> a NoHole piece."""
        info = ExTetromino._find(name)
        if info is None:
            raise ValueError(f"no piece called {name!r}")
        return info.piece_class(info.name, rng=rng)

    # --- per-piece facts ------------------------------------------------------
    @property
    def name(self):
        return self.info.name

    @property
    def spawn_holes(self):
        return self.info.spawn_holes

    def __repr__(self):
        return f"{type(self).__name__}({self.name!r})\n{self}"


# Each difficulty class overrides the constructor (as the brief asks), so that
# its own arguments are documented where a game designer looks for them, and
# so class-specific rules have a natural home. The shared work (choosing the
# piece and its spawn turn) stays in ExTetromino.__init__, reached via super().

class NoHole(ExTetromino):
    """Pieces that appear leaving 0 holes: I, O, L, T, Γ."""
    SPAWN_HOLES = 0

    def __init__(self, variant=None, rng=None):
        """Make a no-hole piece.

        variant: None for a random one; "I", "O", "L", "T" or "Γ"
                 ("Gamma" and "J" also mean Γ); or a number 1-5 in that order.
        rng:     optional random.Random, for replayable games.
        """
        super().__init__(variant, rng)


class OneHole(ExTetromino):
    """Pieces that appear leaving 1 hole: S, Z and eight corner pieces."""
    SPAWN_HOLES = 1

    def __init__(self, variant=None, rng=None):
        """Make a one-hole piece.

        variant: None for a random one; "S", "Z" or "OneHole-01" to
                 "OneHole-08"; or a number 1-10 (1 = S, 2 = Z, 3 = OneHole-01).
        rng:     optional random.Random, for replayable games.
        """
        super().__init__(variant, rng)


class TwoHole(ExTetromino):
    """Pieces that appear leaving 2 holes (all touch at corners)."""
    SPAWN_HOLES = 2

    def __init__(self, variant=None, rng=None):
        """Make a two-hole piece.

        variant: None for a random one; "TwoHole-01" to "TwoHole-11";
                 or a number 1-11.
        rng:     optional random.Random, for replayable games.
        """
        super().__init__(variant, rng)


class ThreeHole(ExTetromino):
    """Pieces that appear leaving 3 holes (all touch at corners)."""
    SPAWN_HOLES = 3

    def __init__(self, variant=None, rng=None):
        """Make a three-hole piece.

        variant: None for a random one; "ThreeHole-01" to "ThreeHole-03";
                 or a number 1-3.
        rng:     optional random.Random, for replayable games.
        """
        super().__init__(variant, rng)


class FourHole(ExTetromino):
    """Pieces that appear leaving 4 holes (all touch at corners)."""
    SPAWN_HOLES = 4

    def __init__(self, variant=None, rng=None):
        """Make a four-hole piece.

        variant: None for a random one; "FourHole-01" to "FourHole-04";
                 or a number 1-4.
        rng:     optional random.Random, for replayable games.
        """
        super().__init__(variant, rng)


class SixHole(ExTetromino):
    """The one piece that appears leaving 6 holes: the long diagonal."""
    SPAWN_HOLES = 6

    def __init__(self, variant=None, rng=None):
        """Make the long diagonal.

        variant: usually left out, since there is only one six-hole piece.
                 None, 1 or "SixHole-01" all give it.
        rng:     optional random.Random; picks which way the diagonal leans
                 (its two spawn turns tie).
        """
        is_number = isinstance(variant, int) and not isinstance(variant, bool)
        if is_number and variant != 1:
            raise ValueError(f"there is only one six-hole piece (SixHole-01), "
                             f"so number {variant} isn't available")
        super().__init__(variant, rng)


DIFFICULTY_CLASSES = (NoHole, OneHole, TwoHole, ThreeHole, FourHole, SixHole)
