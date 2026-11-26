"""Pure functions on piece matrices.

A piece matrix is a 2-D numpy array of booleans (True = filled square).
Every function here returns a NEW read-only array and never changes its input.
This is what prevents the starter code's shared-matrix bugs (B1-B3 in
docs/analysis.md): nothing can be modified in place by accident.
"""
import numpy as np

EDGES = "edges"      # squares joined only through shared sides
CORNERS = "corners"  # at least one square joined only through a corner

_EDGE_STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CORNER_STEPS = _EDGE_STEPS + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def freeze(m):
    """A read-only copy of `m` as a boolean array."""
    out = np.array(m, dtype=bool, copy=True)
    out.flags.writeable = False
    return out


def trim(m):
    """Remove empty border rows and columns. Returns a read-only copy."""
    m = np.asarray(m, dtype=bool)
    if m.ndim != 2 or not m.any():
        raise ValueError("a piece needs a 2-D matrix with at least one filled square")
    rows = np.flatnonzero(m.any(axis=1))
    cols = np.flatnonzero(m.any(axis=0))
    return freeze(m[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1])


def from_cells(cells):
    """Build a trimmed matrix from an iterable of (row, column) pairs."""
    cells = list(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    h = max(r for r, _ in cells) - r0 + 1
    w = max(c for _, c in cells) - c0 + 1
    m = np.zeros((h, w), dtype=bool)
    for r, c in cells:
        m[r - r0, c - c0] = True
    return freeze(m)


def cells(m):
    """The filled squares as a frozenset of (row, column) pairs."""
    return frozenset((int(r), int(c)) for r, c in zip(*np.nonzero(m)))


def key(m):
    """A hashable, sortable identity for one orientation of a piece."""
    m = trim(m)
    return (m.shape, tuple(int(v) for v in m.flat))


def from_key(k):
    shape, flat = k
    return freeze(np.array(flat, dtype=bool).reshape(shape))


# ----------------------------------------------------------------- turns ---
def rotate_cw(m):
    return trim(np.rot90(m, -1))


def rotate_ccw(m):
    return trim(np.rot90(m, 1))


def mirror(m):
    return trim(np.fliplr(m))


def rotations(m):
    """The four quarter-turns, clockwise, starting with `m` itself."""
    out = [trim(m)]
    for _ in range(3):
        out.append(rotate_cw(out[-1]))
    return out


def distinct_rotations(m):
    """The rotations that actually look different, in clockwise order."""
    seen, out = set(), []
    for r in rotations(m):
        k = key(r)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def one_sided_key(m):
    """Same value for a piece in any rotation (mirror images differ)."""
    return min(key(r) for r in rotations(m))


def free_key(m):
    """Same value for a piece in any rotation or mirror image."""
    return min(one_sided_key(m), one_sided_key(mirror(m)))


def is_chiral(m):
    """True if the mirror image can't be reached by rotating."""
    return one_sided_key(m) != one_sided_key(mirror(m))


# ------------------------------------------------------------ properties ---
def touching(m):
    """EDGES if all squares are joined through sides, else CORNERS.

    Raises ValueError if the squares aren't joined even through corners.
    """
    cs = cells(m)

    def connected(steps):
        start = next(iter(cs))
        stack, seen = [start], {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in steps:
                n = (r + dr, c + dc)
                if n in cs and n not in seen:
                    seen.add(n)
                    stack.append(n)
        return seen == cs

    if connected(_EDGE_STEPS):
        return EDGES
    if connected(_CORNER_STEPS):
        return CORNERS
    raise ValueError("squares are not connected")


def box_size(m):
    """Bounding box as 'long x short', e.g. '4x2' (same for every turn)."""
    h, w = trim(m).shape
    return f"{max(h, w)}x{min(h, w)}"


def hole_profile(m):
    """Holes per column when this turn lands on a flat floor.

    In each column, count the empty squares below the column's topmost
    filled square (the piece rests on the bottom of its bounding box).
    """
    m = trim(m)
    out = []
    for c in range(m.shape[1]):
        col = m[:, c]
        top = int(np.argmax(col))
        out.append(int((~col[top:]).sum()))
    return tuple(out)


def holes(m):
    return sum(hole_profile(m))


def spawn_turns(m):
    """The turns a piece may appear in (Phase 2 decision).

    Rule: the flattest turns (least height); among those, the ones with the
    fewest holes. Turns that are still tied are all returned, and the caller
    picks one at random.
    """
    turns = distinct_rotations(m)
    lowest = min(t.shape[0] for t in turns)
    flat = [t for t in turns if t.shape[0] == lowest]
    fewest = min(holes(t) for t in flat)
    return [t for t in flat if holes(t) == fewest]


def spawn_holes(m):
    """Holes left by the spawn turn. This decides a piece's difficulty class."""
    return holes(spawn_turns(m)[0])


def guaranteed_holes(m):
    """Holes the piece leaves on a flat floor in its BEST turn: the holes it
    is sure to leave however the player turns it (6 Nov tutorial)."""
    return min(holes(t) for t in distinct_rotations(m))


def deepest_hole(m):
    """The most empty squares under one column of this turn on a flat floor.
    A deep hole is worse than several shallow ones: it is harder to uncover
    and fill later (6 Nov tutorial)."""
    return max(hole_profile(m))


def box_fill(m):
    """Share of the bounding box that is filled, from 0 to 1 (same for every
    turn). For 4 squares: 1.0 for I and O, 0.25 for the long diagonal."""
    m = trim(m)
    return float(m.sum()) / m.size


def render(m, filled="█", empty="·"):
    return "\n".join("".join(filled if v else empty for v in row) for row in trim(m))
