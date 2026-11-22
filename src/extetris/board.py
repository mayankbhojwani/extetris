"""Board: the grid that pieces land on.

Like Shape, a Board never changes after it is made. place() and
clear_full_rows() return a NEW board. This keeps the "functional" half of the
functional-OO design: the engine (a later phase) can keep the previous board,
try a move, and simply discard the result if it is not wanted.

Positions are (row, col) of the top-left corner of the piece's bounding box.
Row 0 is the top of the board, as in the starter code.

Fixes from the starter's board.py (see docs/analysis.md):
  * B4: fits() checks all four edges explicitly, so a negative row or column
    is "off the board", never a wrap-around to the other side.
  * B10: text output uses one character per square, so rows line up.
"""
import numpy as np

from . import geometry as g

FILLED = "█"
EMPTY = "·"
FALLING = "▒"

MIN_SIZE = 4  # every 4-square piece (even the 4x4 diagonal) must be able to fit


def _matrix_of(piece):
    """Accept a Shape/ExTetromino or a bare matrix."""
    return np.asarray(getattr(piece, "matrix", piece), dtype=bool)


class Board:
    def __init__(self, width=10, height=20, cells=None):
        """An empty board, or one with the given filled squares.

        width, height: whole numbers, at least 4 (default 10 x 20).
        cells:         optional height x width grid of True/False.
        """
        for label, value in (("width", width), ("height", height)):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"{label} must be a whole number")
            if value < MIN_SIZE:
                raise ValueError(f"{label} must be at least {MIN_SIZE} so every "
                                 f"piece fits, not {value}")
        self.width = width
        self.height = height
        if cells is None:
            cells = np.zeros((height, width), dtype=bool)
        cells = g.freeze(cells)
        if cells.shape != (height, width):
            raise ValueError(f"cells must be {height} rows x {width} columns, "
                             f"not {cells.shape[0]} x {cells.shape[1]}")
        self._cells = cells

    @classmethod
    def from_text(cls, text):
        """Build a board from lines of '#'/'█' (filled) and '.'/'·' (empty).

        Handy for tests and for designers sketching a starting position:
            Board.from_text('''
                ....
                #..#
                ####
                ####
            ''')
        """
        rows = [line.strip() for line in text.strip().splitlines() if line.strip()]
        if not rows or len({len(r) for r in rows}) != 1:
            raise ValueError("every row must have the same number of squares")
        grid = []
        for r in rows:
            row = []
            for ch in r:
                if ch in "#" + FILLED:
                    row.append(True)
                elif ch in "." + EMPTY:
                    row.append(False)
                else:
                    raise ValueError(f"unexpected character {ch!r}; use # or .")
            grid.append(row)
        return cls(width=len(rows[0]), height=len(rows), cells=grid)

    # --- looking at the board -------------------------------------------------
    @property
    def cells(self):
        """Read-only height x width numpy array; True = filled."""
        return self._cells

    def is_empty(self):
        return not self._cells.any()

    def fits(self, piece, row, col):
        """True if the piece at (row, col) is fully on the board and overlaps
        nothing already there."""
        m = _matrix_of(piece)
        h, w = m.shape
        if row < 0 or col < 0 or row + h > self.height or col + w > self.width:
            return False
        return not (self._cells[row:row + h, col:col + w] & m).any()

    def drop_row(self, piece, col, row=0):
        """The row the piece would land on if dropped straight down from
        (row, col). None if it doesn't fit there to begin with."""
        if not self.fits(piece, row, col):
            return None
        while self.fits(piece, row + 1, col):
            row += 1
        return row

    def full_rows(self):
        """Indices of completely filled rows, top to bottom."""
        return tuple(int(r) for r in np.flatnonzero(self._cells.all(axis=1)))

    def holes(self):
        """Empty squares that have a filled square somewhere above them in the
        same column (the same rule used for pieces in Phase 1)."""
        total = 0
        for c in range(self.width):
            col = self._cells[:, c]
            if col.any():
                top = int(np.argmax(col))
                total += int((~col[top:]).sum())
        return total

    # --- making new boards ----------------------------------------------------
    def place(self, piece, row, col):
        """A new board with the piece fixed at (row, col).

        Raises ValueError if it doesn't fit; this board is never changed.
        """
        if not self.fits(piece, row, col):
            raise ValueError(f"piece doesn't fit at row {row}, column {col}")
        m = _matrix_of(piece)
        h, w = m.shape
        cells = self._cells.copy()
        cells[row:row + h, col:col + w] |= m
        return Board(self.width, self.height, cells)

    def clear_full_rows(self):
        """(new board, number of rows cleared).

        Full rows disappear, everything above them moves down, and empty
        rows are added at the top.
        """
        full = self._cells.all(axis=1)
        n = int(full.sum())
        if n == 0:
            return self, 0
        kept = self._cells[~full]
        cells = np.vstack([np.zeros((n, self.width), dtype=bool), kept])
        return Board(self.width, self.height, cells), n

    # --- display and comparison -----------------------------------------------
    def render(self, piece=None, row=0, col=0):
        """Text picture of the board, one character per square.

        If a piece is given it is drawn with '▒' at (row, col) without being
        placed, e.g. to show the piece that is still falling.
        """
        grid = [[FILLED if v else EMPTY for v in r] for r in self._cells]
        if piece is not None:
            if not self.fits(piece, row, col):
                raise ValueError(f"piece doesn't fit at row {row}, column {col}")
            for r, c in g.cells(_matrix_of(piece)):
                grid[row + r][col + c] = FALLING
        return "\n".join("".join(r) for r in grid)

    def __str__(self):
        return self.render()

    def __repr__(self):
        return f"Board(width={self.width}, height={self.height})\n{self}"

    def __eq__(self, other):
        if not isinstance(other, Board):
            return NotImplemented
        return np.array_equal(self._cells, other.cells)

    def __hash__(self):
        return hash((self._cells.shape, self._cells.tobytes()))
