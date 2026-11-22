"""GameWindow: a tkinter window that shows a Game and passes keys to it.

All the rules live in game.Game; this file only draws and listens.

Fixes from the starter's engine.py (see docs/analysis.md):
  * B6:  exactly one gravity timer; it is cancelled before being rescheduled,
         so pressing keys while paused can't start extra timers.
  * B5:  "About" restores the pause state it found (no pasueStatus typo).
  * B10: squares are drawn on a Canvas, so nothing wraps or misaligns.
  * D2:  messagebox and filedialog are imported explicitly.
  * L2:  anticlockwise turning has a key (Z).
  * L5:  the picture is redrawn only when something changes.
"""
import tkinter as tk
from tkinter import filedialog, messagebox

from .game import Game
from .mixes import MODES

MODE_NAMES = list(MODES) + ["progressive"]

# One colour per difficulty class, so players can see how awkward a piece is.
CLASS_COLOURS = {
    "NoHole": "#43a047",     # green
    "OneHole": "#1e88e5",    # blue
    "TwoHole": "#8e24aa",    # purple
    "ThreeHole": "#fb8c00",  # orange
    "FourHole": "#e53935",   # red
    "SixHole": "#212121",    # black
}
DEFAULT_PIECE_COLOUR = "#00897b"
SETTLED_COLOUR = "#78909c"
GRID_COLOUR = "#e0e0e0"
BACKGROUND = "#fafafa"

KEYS_HELP = """Left / Right   move
Up             turn clockwise
Z              turn anticlockwise
Down           move down one row
Space          drop to the bottom
P              pause / resume

Pieces menu: choose which pieces appear (Classic ... Chaos).
Progressive starts with classic pieces and adds harder ones
every 10 lines."""


class GameWindow:
    """A window to play a Game in: draws it and sends key presses to it."""

    def __init__(self, game=None, cell_size=28, title="ExTetris", master=None):
        """A window for `game` (a new default Game if none is given).

        cell_size: size of one square in pixels.
        master:    an existing tk.Tk to draw into (optional).
        """
        self.game = game or Game()
        self.cell = cell_size
        self.root = master or tk.Tk()
        self.root.title(title)
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=self.game.width * cell_size,
                                height=self.game.height * cell_size,
                                bg=BACKGROUND, highlightthickness=0)
        self.canvas.pack(padx=8, pady=8)
        self.status = tk.StringVar(self.root)
        tk.Label(self.root, textvariable=self.status).pack(pady=(0, 8))

        self._build_menu()
        self._bind_keys()
        self._after_id = None
        self._schedule_gravity()
        self.redraw()

    def run(self):
        """Open the window and play until it is closed."""
        self.root.mainloop()

    # --- input -------------------------------------------------------------------
    def _bind_keys(self):
        g = self.game
        bindings = {
            "<Left>": g.move_left, "<Right>": g.move_right,
            "<Up>": g.rotate_cw, "<z>": g.rotate_ccw, "<Z>": g.rotate_ccw,
            "<Down>": g.soft_drop, "<space>": g.hard_drop,
            "<p>": g.toggle_pause, "<P>": g.toggle_pause,
        }
        for key, action in bindings.items():
            self.root.bind(key, lambda event, a=action: self._do(a))

    def _do(self, action):
        action()
        self.redraw()
        return "break"

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        game_menu = tk.Menu(menubar, tearoff=False)
        game_menu.add_command(label="New Game", command=self.new_game)
        game_menu.add_command(label="Pause / Resume",
                              command=lambda: self._do(self.game.toggle_pause))
        game_menu.add_separator()
        game_menu.add_command(label="Speed Up",
                              command=lambda: self._do(self.game.speed_up))
        game_menu.add_command(label="Slow Down",
                              command=lambda: self._do(self.game.slow_down))
        game_menu.add_separator()
        game_menu.add_command(label="Save Board as Text…", command=self.save_board)
        game_menu.add_separator()
        game_menu.add_command(label="Quit", command=self.root.destroy)
        menubar.add_cascade(label="Game", menu=game_menu)

        self.mode_var = tk.StringVar(self.root, value=self.game.pieces_name)
        pieces_menu = tk.Menu(menubar, tearoff=False)
        for name in MODE_NAMES:
            pieces_menu.add_radiobutton(label=name.capitalize(), value=name,
                                        variable=self.mode_var,
                                        command=lambda n=name: self.set_mode(n))
        menubar.add_cascade(label="Pieces", menu=pieces_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Keys", command=self.show_keys)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)

    # --- timer -------------------------------------------------------------------
    def _schedule_gravity(self):
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(self.game.delay_ms, self._gravity)

    def _gravity(self):
        # _schedule_gravity cancels whatever timer is recorded, so even a
        # direct call here can never leave two timers running.
        self.game.tick()
        self.redraw()
        self._schedule_gravity()

    # --- menu actions --------------------------------------------------------------
    def new_game(self):
        """Start a fresh game (menu: Game > New Game)."""
        self.game.new_game()
        self._schedule_gravity()
        self.redraw()

    def set_mode(self, name):
        """Switch the piece mix; it applies from the piece after next."""
        self.game.set_pieces(name)
        self.mode_var.set(name)
        self.redraw()

    def save_board(self):
        """Ask for a file name and save the board as text."""
        was_paused = self.game.paused
        self.game.set_paused(True)
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.game.render() + "\n")
        self.game.set_paused(was_paused)
        self.redraw()

    def _dialog(self, title, text):
        was_paused = self.game.paused
        self.game.set_paused(True)
        self.redraw()
        messagebox.showinfo(title, text, parent=self.root)
        self.game.set_paused(was_paused)
        self.redraw()

    def show_keys(self):
        """Show the list of keys (menu: Help > Keys)."""
        self._dialog("Keys", KEYS_HELP)

    def show_about(self):
        """Show the About box (menu: Help > About)."""
        self._dialog("About ExTetris",
                     "ExTetris: Tetris with pieces that may touch at corners.\n"
                     "Piece colour shows its difficulty class "
                     "(green = no holes ... black = six holes).\n\n"
                     "Built on the EXtendedTETRIckS starter code by "
                     "Ramprasad S. Joshi (GPL-3.0).")

    # --- drawing -------------------------------------------------------------------
    def _square(self, row, col, fill):
        x, y = col * self.cell, row * self.cell
        self.canvas.create_rectangle(x + 1, y + 1, x + self.cell - 1,
                                     y + self.cell - 1, fill=fill, outline="")

    def redraw(self):
        """Draw the board, the falling piece and the status line again."""
        g, c = self.game, self.canvas
        c.delete("all")
        for x in range(g.width + 1):
            c.create_line(x * self.cell, 0, x * self.cell, g.height * self.cell,
                          fill=GRID_COLOUR)
        for y in range(g.height + 1):
            c.create_line(0, y * self.cell, g.width * self.cell, y * self.cell,
                          fill=GRID_COLOUR)
        for row, col in zip(*g.board.cells.nonzero()):
            self._square(int(row), int(col), SETTLED_COLOUR)
        if not g.game_over:
            colour = CLASS_COLOURS.get(type(g.piece).__name__, DEFAULT_PIECE_COLOUR)
            for r, col in g.piece.cells:
                self._square(g.row + r, g.col + col, colour)

        mid_x, mid_y = g.width * self.cell / 2, g.height * self.cell / 2
        if g.game_over:
            c.create_text(mid_x, mid_y, text="GAME OVER\nGame ▸ New Game",
                          justify="center", font=("Helvetica", 18, "bold"))
        elif g.paused:
            c.create_text(mid_x, mid_y, text="PAUSED", font=("Helvetica", 18, "bold"))

        name = getattr(g.piece, "name", type(g.piece).__name__)
        nxt = getattr(g.next_piece, "name", type(g.next_piece).__name__)
        self.status.set(f"Lines: {g.lines}   Placed: {g.pieces_placed}   "
                        f"Fall delay: {g.delay_ms} ms   Pieces: {g.pieces_name}\n"
                        f"Now: {name} ({type(g.piece).__name__})   Next: {nxt}")
