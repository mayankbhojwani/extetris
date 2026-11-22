"""PieceGenerator: builds every piece from a rule instead of a hand-typed list.

Example:
    PieceGenerator(n_cells=4, touching="corners").shapes()   # 34 pieces
    PieceGenerator(n_cells=4, touching="edges").shapes()     # 7 classic pieces
"""
from . import geometry as g


class PieceGenerator:
    """All shapes made of `n_cells` squares joined by `touching`.

    touching = "edges"   -> squares must share sides (classic Tetris pieces)
    touching = "corners" -> squares may also meet only at a corner

    shapes() lists each piece once per rotation class (mirror images are
    separate pieces), in a fixed order, so names and settings stay stable
    between runs.
    """

    def __init__(self, n_cells=4, touching=g.CORNERS):
        if n_cells < 1:
            raise ValueError("n_cells must be at least 1")
        if touching not in (g.EDGES, g.CORNERS):
            raise ValueError(f"touching must be {g.EDGES!r} or {g.CORNERS!r}")
        self.n_cells = n_cells
        self.touching = touching
        self._shapes = None

    def _neighbour_steps(self):
        steps = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if self.touching == g.CORNERS:
            steps += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return steps

    def _all_fixed(self):
        """Every orientation of every shape, grown one square at a time."""
        steps = self._neighbour_steps()
        frontier = {frozenset({(0, 0)})}
        for _ in range(self.n_cells - 1):
            grown = set()
            for shape in frontier:
                for r, c in shape:
                    for dr, dc in steps:
                        n = (r + dr, c + dc)
                        if n not in shape:
                            grown.add(frozenset(shape | {n}))
            frontier = grown
        return {g.key(g.from_cells(s)) for s in frontier}

    def shapes(self):
        """One matrix per piece (rotations merged), in a fixed order.

        Each matrix is the piece's standard turn (the smallest key over its
        rotations). Use geometry.spawn_turns() to find how it should appear.
        """
        if self._shapes is None:
            one_sided = {g.one_sided_key(g.from_key(k)) for k in self._all_fixed()}
            self._shapes = tuple(g.from_key(k) for k in sorted(one_sided))
        return self._shapes

    def free_shapes(self):
        """One matrix per piece with rotations AND mirror images merged."""
        seen, out = set(), []
        for m in self.shapes():
            k = g.free_key(m)
            if k not in seen:
                seen.add(k)
                out.append(m)
        return tuple(out)

    def __repr__(self):
        return f"PieceGenerator(n_cells={self.n_cells}, touching={self.touching!r})"
