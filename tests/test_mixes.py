"""Phase 5 tests: piece mixes (which pieces appear, and how often).

Run from the project root:
    python3 -B -m unittest discover -s tests -v
"""
import random
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from extetris import (MODES, ExTetromino, Game, NoHole, PieceMix,  # noqa: E402
                      mix, mode, only, progressive)

CLASSICS = {"I", "O", "T", "S", "Z", "L", "Γ"}


class TestMix(unittest.TestCase):
    def test_class_weight_is_shared_by_its_pieces(self):
        m = mix(NoHole=60, OneHole=40)
        self.assertAlmostEqual(m.probabilities_by_class()["NoHole"], 0.6)
        self.assertAlmostEqual(m.probabilities_by_class()["OneHole"], 0.4)
        self.assertAlmostEqual(m.probabilities()["T"], 0.6 / 5)
        self.assertAlmostEqual(m.probabilities()["S"], 0.4 / 10)

    def test_replaces_the_repeat_the_index_trick(self):
        # Starter: list I three times and O once. Here: just say so.
        m = mix({"I": 3, "O": 1})
        self.assertEqual(m.probabilities(), {"I": 0.75, "O": 0.25})

    def test_names_aliases_classes_and_groups(self):
        self.assertEqual(set(mix({"Gamma": 1}).probabilities()), {"Γ"})
        self.assertEqual(set(mix({"TwoHole-03": 1}).probabilities()), {"TwoHole-03"})
        self.assertEqual(set(mix(classic=1).probabilities()), CLASSICS)
        self.assertEqual(len(mix(all=1).probabilities()), 34)
        self.assertEqual(set(mix({NoHole: 1}).probabilities()), {"I", "O", "L", "T", "Γ"})

    def test_overlapping_groups_add_up(self):
        m = mix(classic=7, S=1)        # S gets 1/7 * 7 = 1, plus 1
        p = m.probabilities()
        self.assertAlmostEqual(p["S"], 2 * p["T"])

    def test_bad_mixes_are_rejected(self):
        with self.assertRaises(ValueError):
            mix(Nonsense=1)
        with self.assertRaises(ValueError):
            mix(NoHole=-1)
        with self.assertRaises(ValueError):
            mix(NoHole=0)
        with self.assertRaises(ValueError):
            mix()

    def test_only(self):
        self.assertEqual(only("I", "O").probabilities(), {"I": 0.5, "O": 0.5})

    def test_draws_follow_the_chances(self):
        m = mix(NoHole=70, TwoHole=30)
        rng = random.Random(5)
        counts = Counter(type(m.draw(rng)).__name__ for _ in range(5000))
        self.assertAlmostEqual(counts["NoHole"] / 5000, 0.7, delta=0.03)
        self.assertEqual(set(counts), {"NoHole", "TwoHole"})

    def test_custom_weight_function(self):
        # The functional part: any function (piece info, lines) -> weight.
        wide_only = PieceMix(lambda info, lines: info.box_size.startswith("4"),
                             name="long pieces")
        for name in wide_only.probabilities():
            self.assertTrue(ExTetromino._find(name).box_size.startswith("4"))


class TestModes(unittest.TestCase):
    def test_every_mode_adds_up_to_one(self):
        for name, m in MODES.items():
            self.assertAlmostEqual(sum(m.probabilities().values()), 1.0, msg=name)
            self.assertEqual(m.name, name)

    def test_classic_is_the_seven_classics(self):
        self.assertEqual(set(MODES["classic"].probabilities()), CLASSICS)

    def test_chaos_is_all_34_equally(self):
        p = MODES["chaos"].probabilities()
        self.assertEqual(len(p), 34)
        self.assertTrue(all(abs(v - 1 / 34) < 1e-12 for v in p.values()))

    def test_easy_has_no_pieces_beyond_one_hole(self):
        classes = set(MODES["easy"].probabilities_by_class())
        self.assertLessEqual(classes, {"NoHole", "OneHole"})

    def test_modes_get_harder_in_order(self):
        holes = [MODES[n].expected_holes() for n in
                 ("classic", "easy", "normal", "hard", "chaos")]
        self.assertEqual(holes, sorted(holes))
        self.assertEqual(len(set(holes)), 5)

    def test_mode_lookup(self):
        self.assertIs(mode("easy"), MODES["easy"])
        self.assertEqual(mode("progressive").name, "progressive")
        with self.assertRaises(ValueError):
            mode("impossible")


class TestProgressive(unittest.TestCase):
    def test_default_stages(self):
        p = progressive()
        self.assertEqual(set(p.probabilities(lines=0)), CLASSICS)
        self.assertEqual(p.probabilities(lines=9), MODES["classic"].probabilities())
        self.assertEqual(p.probabilities(lines=10), MODES["easy"].probabilities())
        self.assertEqual(p.probabilities(lines=25), MODES["normal"].probabilities())
        self.assertEqual(p.probabilities(lines=1000), MODES["hard"].probabilities())

    def test_custom_stages(self):
        p = progressive(["classic", mix(TwoHole=1)], every_lines=3)
        self.assertEqual(set(p.probabilities(2)), CLASSICS)
        self.assertEqual(set(p.probabilities_by_class(3)), {"TwoHole"})

    def test_bad_settings(self):
        with self.assertRaises(ValueError):
            progressive(every_lines=0)
        with self.assertRaises(ValueError):
            progressive([])


class TestGameUsesMixes(unittest.TestCase):
    def test_default_game_starts_with_classic_pieces(self):
        g = Game(rng=random.Random(1))
        self.assertEqual(g.pieces_name, "progressive")
        for _ in range(100):
            self.assertIn(g.piece.name, CLASSICS)
            g.hard_drop()
            if g.game_over:
                g.new_game()

    def test_progressive_changes_with_lines(self):
        g = Game(rng=random.Random(2))
        g.lines = 40                         # into the "hard" stage
        seen = {type(g._draw()).__name__ for _ in range(300)}
        self.assertTrue(seen - {"NoHole", "OneHole"})

    def test_mode_by_name_or_mix_or_function(self):
        self.assertEqual(Game(pieces="chaos").pieces_name, "chaos")
        self.assertEqual(Game(pieces=mix(TwoHole=1)).pieces_name, "custom")
        g = Game(pieces=lambda rng: NoHole("O"))
        self.assertEqual(g.piece.name, "O")
        with self.assertRaises(ValueError):
            Game(pieces="impossible")
        with self.assertRaises(TypeError):
            Game(pieces=42)

    def test_switching_mode_mid_game(self):
        g = Game(pieces="classic", rng=random.Random(3))
        g.set_pieces("chaos")
        self.assertEqual(g.pieces_name, "chaos")
        names = {g._draw().name for _ in range(400)}
        self.assertTrue(names - CLASSICS)


if __name__ == "__main__":
    unittest.main()
