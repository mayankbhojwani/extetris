"""A wide board with a hand-made piece mix.

Run it:   python3 examples/wide_board_custom_mix.py

The mix says what share of pieces come from each group:
  * "classic" = the 7 normal pieces (I, O, T, S, Z, L, Γ)
  * a class name such as "TwoHole" = all pieces in that class
  * a single piece name such as "I" or "TwoHole-03"
The numbers don't have to add up to 100; they're shares.
See all piece names with:  python3 play.py --catalogue
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from extetris import Game, mix  # noqa: E402


def make_game():
    return Game(
        width=14, height=22,
        pieces=mix(classic=70, TwoHole=20, I=10),   # extra long bars
        start_delay_ms=800,                          # a bit quicker from the start
    )


if __name__ == "__main__":
    from extetris.window import GameWindow
    GameWindow(make_game(), title="ExTetris - Wide Board", cell_size=24).run()
