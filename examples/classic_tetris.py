"""Classic Tetris: only the 7 normal pieces, on the usual 10 x 20 board.

Run it:   python3 examples/classic_tetris.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from extetris import Game  # noqa: E402


def make_game():
    return Game(pieces="classic")


if __name__ == "__main__":
    from extetris.window import GameWindow
    GameWindow(make_game(), title="Classic Tetris").run()
