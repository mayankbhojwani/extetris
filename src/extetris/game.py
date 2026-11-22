"""Game: the rules of ExTetris, with no window attached.

Keeping the rules separate from the window (unlike the starter's single
TetrisEngine class) means the game can be tested, replayed with a fixed random
seed, or given a different front end, without touching tkinter.

Fixes from the starter's engine.py (see docs/analysis.md):
  * B5/B7: pause and game over are plain flags on the Game, set in one place.
  * B8:    speed-ups count every multiple of `speedup_every` lines crossed,
           even when several rows clear at once (e.g. 99 -> 101).
  * L1:    turning keeps the piece centred and tries small sideways/upward
           shifts ("wall kicks") so pieces can turn next to a wall.
  * L3:    hard drop locks the piece immediately.
  * B1/B2: impossible here, because pieces and boards never change.
"""
import random

from .board import Board
from .mixes import PieceMix, mode
from .pieces import ExTetromino
from .shape import Shape

# Shifts (rows, columns) tried in order when a turn doesn't fit in place.
KICKS = ((0, 0), (0, -1), (0, 1), (0, -2), (0, 2), (-1, 0))


def any_piece(rng):
    """Every one of the 34 pieces equally likely (the same as mode "chaos")."""
    info = rng.choice(ExTetromino.catalogue())
    return info.piece_class(info.name, rng=rng)


class Game:
    """One game of ExTetris: the board, the falling piece, score and speed.

    Every move method returns True if it changed something, False if it
    was blocked (by a wall, another piece, pause or game over).
    """

    def __init__(self, width=10, height=20, pieces="progressive", rng=None,
                 start_delay_ms=1000, speedup_every=100, speedup_factor=0.9,
                 min_delay_ms=50):
        """A new game, ready to play.

        width, height:   board size (default 10 x 20, as in the starter).
        pieces:          which pieces appear and how often. One of:
                           * a mode name: "classic", "easy", "normal",
                             "hard", "chaos" or "progressive" (default:
                             classic pieces first, harder ones as lines
                             are cleared);
                           * a PieceMix, e.g. mix(NoHole=60, OneHole=40);
                           * any function rng -> piece.
        rng:             random.Random; pass one with a seed to replay a game.
        start_delay_ms:  time between automatic one-row falls at the start.
        speedup_every:   lines to clear for each automatic speed-up
                         (default 100, as in the starter).
        speedup_factor:  each speed-up multiplies the delay by this.
        min_delay_ms:    the delay never goes below this.
        """
        if not 0 < speedup_factor <= 1:
            raise ValueError("speedup_factor must be between 0 and 1")
        if speedup_every < 1:
            raise ValueError("speedup_every must be at least 1")
        self.width = width
        self.height = height
        self.set_pieces(pieces)
        self.rng = rng or random.Random()
        self.start_delay_ms = start_delay_ms
        self.speedup_every = speedup_every
        self.speedup_factor = speedup_factor
        self.min_delay_ms = min_delay_ms
        self.new_game()

    # --- starting ----------------------------------------------------------------
    def new_game(self):
        """Empty the board and start again (also works after game over)."""
        self.board = Board(self.width, self.height)
        self.lines = 0
        self.pieces_placed = 0
        self.delay_ms = self.start_delay_ms
        self.paused = False
        self.game_over = False
        self.next_piece = self._draw()
        self._spawn()

    def set_pieces(self, pieces):
        """Change the piece mix; it applies from the next piece drawn."""
        if isinstance(pieces, str):
            pieces = mode(pieces)
        if not callable(pieces):
            raise TypeError("pieces must be a mode name, a PieceMix or a function")
        self.pieces = pieces

    @property
    def pieces_name(self):
        """Name of the current piece mix, e.g. "progressive"."""
        return getattr(self.pieces, "name", "custom")

    def _draw(self):
        if isinstance(self.pieces, PieceMix):
            piece = self.pieces.draw(self.rng, self.lines)
        else:
            piece = self.pieces(self.rng)
        if not isinstance(piece, Shape):
            raise TypeError("pieces must produce a piece (a Shape)")
        return piece

    def _spawn(self):
        """Bring in the next piece at the top centre; game over if it can't fit."""
        self.piece = self.next_piece
        self.next_piece = self._draw()
        self.row = 0
        self.col = (self.width - self.piece.width) // 2
        if not self.board.fits(self.piece, self.row, self.col):
            self.game_over = True

    # --- state -------------------------------------------------------------------
    @property
    def active(self):
        """True while the player can move pieces."""
        return not (self.paused or self.game_over)

    def set_paused(self, paused):
        """Pause (True) or resume (False). Ignored after game over."""
        if not self.game_over:
            self.paused = bool(paused)

    def toggle_pause(self):
        """Pause if running, resume if paused."""
        self.set_paused(not self.paused)

    # --- player moves (each returns True if something changed) -------------------
    def move_left(self):
        """Move the falling piece one column left."""
        return self.active and self._move_to(self.piece, self.row, self.col - 1)

    def move_right(self):
        """Move the falling piece one column right."""
        return self.active and self._move_to(self.piece, self.row, self.col + 1)

    def rotate_cw(self):
        """Turn the falling piece clockwise (with wall kicks)."""
        return self.active and self._turn_to(self.piece.rotated_cw())

    def rotate_ccw(self):
        """Turn the falling piece anticlockwise (with wall kicks)."""
        return self.active and self._turn_to(self.piece.rotated_ccw())

    def soft_drop(self):
        """One row down now; locks the piece if it is already resting."""
        return self.tick()

    def hard_drop(self):
        """Straight to the bottom and lock immediately."""
        if not self.active:
            return False
        self.row = self.board.drop_row(self.piece, self.col, self.row)
        self._lock()
        return True

    def tick(self):
        """One step of gravity: fall one row, or lock if resting on something."""
        if not self.active:
            return False
        if not self._move_to(self.piece, self.row + 1, self.col):
            self._lock()
        return True

    # --- speed (also used by the menu) -------------------------------------------
    def speed_up(self, times=1):
        """Make pieces fall faster: delay x speedup_factor, `times` times."""
        delay = self.delay_ms * self.speedup_factor ** times
        self.delay_ms = max(self.min_delay_ms, int(delay))

    def slow_down(self):
        """Undo one speed-up: delay / speedup_factor."""
        self.delay_ms = int(round(self.delay_ms / self.speedup_factor))

    # --- internals ---------------------------------------------------------------
    def _move_to(self, piece, row, col):
        if self.board.fits(piece, row, col):
            self.piece, self.row, self.col = piece, row, col
            return True
        return False

    def _turn_to(self, turned):
        # keep the turned piece centred where the old one was
        row = max(0, self.row + (self.piece.height - turned.height) // 2)
        col = self.col + (self.piece.width - turned.width) // 2
        return any(self._move_to(turned, row + dr, col + dc) for dr, dc in KICKS)

    def _lock(self):
        self.board = self.board.place(self.piece, self.row, self.col)
        self.board, cleared = self.board.clear_full_rows()
        before = self.lines
        self.lines += cleared
        crossed = self.lines // self.speedup_every - before // self.speedup_every
        if crossed:
            self.speed_up(crossed)
        self.pieces_placed += 1
        self._spawn()

    # --- display -----------------------------------------------------------------
    def render(self):
        """Text picture of the board with the falling piece shown as '▒'."""
        if self.game_over:
            return self.board.render()
        return self.board.render(self.piece, self.row, self.col)
