"""Shape: the base class for every piece. It knows its squares and can turn.

Unlike the starter's Shape, a Shape here never changes after it is made.
rotated_cw() and rotated_ccw() return a NEW piece, so a blocked rotation
can't damage the piece that is already on the board, and no two pieces ever
share one matrix (fixes starter bugs B1, B2 and B3).
"""
import copy

from . import geometry as g


class Shape:
    def __init__(self, matrix):
        self._matrix = g.trim(matrix)

    # --- what the piece looks like now --------------------------------------
    @property
    def matrix(self):
        """Read-only boolean numpy array of the current turn."""
        return self._matrix

    @property
    def height(self):
        return self._matrix.shape[0]

    @property
    def width(self):
        return self._matrix.shape[1]

    @property
    def cells(self):
        """Filled squares as (row, column) pairs, relative to the top-left."""
        return g.cells(self._matrix)

    @property
    def hole_profile(self):
        """Holes per column if this turn landed on a flat floor."""
        return g.hole_profile(self._matrix)

    @property
    def holes(self):
        """Holes if this turn landed on a flat floor."""
        return g.holes(self._matrix)

    # --- what stays the same whichever way it is turned ----------------------
    @property
    def box_size(self):
        """Bounding box as 'long x short', e.g. '4x2'."""
        return g.box_size(self._matrix)

    @property
    def touching(self):
        """'edges' or 'corners'."""
        return g.touching(self._matrix)

    @property
    def is_chiral(self):
        """True if the piece has a separate mirror-image twin."""
        return g.is_chiral(self._matrix)

    # --- turning: always returns a new object --------------------------------
    def rotated_cw(self):
        return self._with_matrix(g.rotate_cw(self._matrix))

    def rotated_ccw(self):
        return self._with_matrix(g.rotate_ccw(self._matrix))

    def _with_matrix(self, matrix):
        """A copy of this piece (same class, name, etc.) in another turn."""
        new = copy.copy(self)
        new._matrix = g.freeze(matrix)
        return new

    # --- comparison and display ----------------------------------------------
    def same_piece_as(self, other):
        """True if `other` is this piece in any rotation."""
        return g.one_sided_key(self._matrix) == g.one_sided_key(other.matrix)

    def __eq__(self, other):
        """Equal if same class and the same squares in the same turn."""
        if not isinstance(other, Shape):
            return NotImplemented
        return type(self) is type(other) and g.key(self._matrix) == g.key(other.matrix)

    def __hash__(self):
        return hash((type(self), g.key(self._matrix)))

    def __str__(self):
        return g.render(self._matrix)

    def __repr__(self):
        return f"{type(self).__name__}(\n{self}\n)"
