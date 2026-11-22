"""Gentle start: easy pieces for a while, then harder ones, and faster sooner.

Run it:   python3 examples/gentle_start.py

Things to try changing:
  * every_lines   how many lines before the next, harder stage
  * the stages    any of "classic", "easy", "normal", "hard", "chaos"
  * speedup_every how many lines before pieces fall faster
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from extetris import Game, progressive  # noqa: E402


def make_game():
    return Game(
        pieces=progressive(["classic", "easy", "normal"], every_lines=5),
        speedup_every=10,        # faster every 10 lines (default is 100)
        speedup_factor=0.85,     # each time, 15 % less waiting between falls
    )


if __name__ == "__main__":
    from extetris.window import GameWindow
    GameWindow(make_game(), title="ExTetris - Gentle Start").run()
