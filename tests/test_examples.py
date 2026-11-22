"""The examples in examples/ (used by the manual) must keep working.

Run from the project root:
    python3 -B -m unittest discover -s tests -v
"""
import importlib.util
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from extetris import Game  # noqa: E402


def load(name):
    spec = importlib.util.spec_from_file_location(f"_example_{name}",
                                                  ROOT / "examples" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestExamples(unittest.TestCase):
    def test_every_example_makes_a_playable_game(self):
        files = sorted(p.stem for p in (ROOT / "examples").glob("*.py"))
        self.assertGreaterEqual(len(files), 3)
        for name in files:
            g = load(name).make_game()
            self.assertIsInstance(g, Game, name)
            for _ in range(30):
                g.hard_drop()
                if g.game_over:
                    g.new_game()

    def test_classic_only_gives_classic_pieces(self):
        g = load("classic_tetris").make_game()
        self.assertEqual(g.pieces_name, "classic")

    def test_wide_board_settings(self):
        g = load("wide_board_custom_mix").make_game()
        self.assertEqual((g.width, g.height, g.delay_ms), (14, 22, 800))


class TestManualSnippets(unittest.TestCase):
    """Code shown in docs/manual.md section 5-6."""

    def test_snippets_run(self):
        from extetris import NoHole, PieceMix, mix, only, progressive
        Game(pieces="hard")
        Game(pieces=mix(classic=70, TwoHole=20, I=10))
        Game(pieces=mix({"TwoHole-03": 5, "Γ": 2, "classic": 50}))
        Game(pieces=only("I", "O", "T"))
        Game(pieces=progressive(["classic", "easy", "hard"], every_lines=5))
        rule = PieceMix(lambda info, lines: (1 + lines)
                        if info.box_size.startswith("3") else 0)
        Game(pieces=rule)
        Game(pieces=lambda rng: NoHole("T", rng=rng))
        g = Game()
        g.move_left()
        g.hard_drop()
        self.assertIn("▒", g.render())


if __name__ == "__main__":
    unittest.main()
