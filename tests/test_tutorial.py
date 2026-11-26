"""Phase 9 tests: what the 6 Nov tutorial asked for.

  * more ways to classify pieces: guaranteed holes (in any turn), deepest
    hole, bounding box size and how full the bounding box is;
  * piece chances that look at the board: fair, assistive and unfair games.

Run from the project root:
    python3 -B -m unittest discover -s tests -v
"""
import json
import random
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from extetris import (Board, BoardAwareMix, ExTetromino, Game,  # noqa: E402
                      assistive, fair, mix, mode, unfair)
from extetris import geometry as g  # noqa: E402
from extetris.generator import PieceGenerator  # noqa: E402
from extetris.mixes import _group, new_holes, property_groups  # noqa: E402
from extetris.playtest import playtest  # noqa: E402
from extetris.variant import Variant  # noqa: E402

# A board with a one-column well on the right: I fills it without holes,
# S and Z can't be placed anywhere without leaving one.
WELL = Board.from_text("""
    ..........
    ..........
    ..........
    #########.
    #########.
    #########.
    #########.
""")


def names(group):
    return {i.name for i in group}


class TestNewProperties(unittest.TestCase):
    def test_measures_on_simple_turns(self):
        diagonal = g.from_cells([(0, 0), (1, 1), (2, 2), (3, 3)])
        self.assertEqual(g.box_fill(diagonal), 0.25)
        self.assertEqual(g.deepest_hole(diagonal), 3)
        self.assertEqual(g.guaranteed_holes(diagonal), 6)
        o = g.from_cells([(0, 0), (0, 1), (1, 0), (1, 1)])
        self.assertEqual((g.box_fill(o), g.deepest_hole(o), g.guaranteed_holes(o)),
                         (1.0, 0, 0))

    def test_four_squares_guaranteed_equals_spawn_holes(self):
        # Finding of Phase 9: the spawn-turn rule already picks a turn with
        # the fewest holes, so for 4 squares the two classifications agree.
        for info in ExTetromino.catalogue():
            self.assertEqual(info.guaranteed_holes, info.spawn_holes, info.name)

    def test_five_squares_can_differ(self):
        differ = [m for m in PieceGenerator(n_cells=5, touching=g.CORNERS).shapes()
                  if g.guaranteed_holes(m) != g.spawn_holes(m)]
        self.assertEqual(len(differ), 8)
        for m in differ:
            self.assertLess(g.guaranteed_holes(m), g.spawn_holes(m))

    def test_catalogue_values(self):
        by = {i.name: i for i in ExTetromino.catalogue()}
        self.assertEqual(by["SixHole-01"].deepest_hole, 3)
        self.assertEqual(by["I"].box_fill, 1.0)
        self.assertAlmostEqual(by["T"].box_fill, 2 / 3)


class TestPropertyGroups(unittest.TestCase):
    def test_box_group(self):
        self.assertEqual(names(_group("box:4x1")), {"I"})
        self.assertEqual(names(_group("box:1x4")), {"I"})   # order doesn't matter
        self.assertEqual(len(_group("box:3x3")), 9)

    def test_fill_group(self):
        self.assertEqual(names(_group("fill>=100")), {"I", "O"})
        self.assertEqual(len(_group("fill>=25")), 34)

    def test_guaranteed_and_deepest_groups(self):
        self.assertEqual(names(_group("guaranteed:0")), {"I", "O", "L", "T", "Γ"})
        self.assertEqual(names(_group("deepest:3")), {"SixHole-01"})
        self.assertEqual(len(_group("deepest:2")), 8)   # worst spawn turn counts

    def test_empty_or_bad_groups_are_rejected(self):
        for key in ("box:5x5", "deepest:9", "box:big", "fill>50"):
            with self.assertRaises(ValueError):
                _group(key)

    def test_every_listed_group_has_pieces(self):
        for key in property_groups():
            self.assertTrue(_group(key), key)

    def test_groups_work_in_mixes_and_variants(self):
        m = mix({"box:3x3": 1})
        self.assertEqual(set(m.probabilities()), names(_group("box:3x3")))
        v = Variant({"name": "x", "pieces": {"kind": "mix",
                                             "weights": {"deepest:2": 1, "fill>=100": 1}}})
        self.assertEqual(v.problems(), [])
        bad = Variant({"name": "x", "pieces": {"kind": "mix", "weights": {"box:9x9": 1}}})
        self.assertTrue(bad.problems())


class TestBoardAware(unittest.TestCase):
    def test_new_holes(self):
        self.assertEqual(new_holes(WELL, ExTetromino._find("I")), 0)
        self.assertGreater(new_holes(WELL, ExTetromino._find("S")), 0)
        full = Board.from_text("####\n####\n####\n###.")
        self.assertIsNone(new_holes(full, ExTetromino._find("O")))

    def test_assistive_prefers_pieces_that_fit(self):
        probs = assistive("classic").probabilities(0, WELL)
        self.assertNotIn("S", probs)
        self.assertNotIn("Z", probs)
        self.assertIn("I", probs)

    def test_unfair_prefers_pieces_that_dont_fit(self):
        self.assertEqual(set(unfair("classic").probabilities(0, WELL)), {"S", "Z"})

    def test_strength_keeps_some_chance_for_the_rest(self):
        plain = mode("classic").probabilities()
        half = assistive("classic", 0.5).probabilities(0, WELL)
        self.assertEqual(set(half), set(plain))
        self.assertLess(half["S"], plain["S"])
        self.assertGreater(half["I"], plain["I"])
        self.assertAlmostEqual(sum(half.values()), 1)

    def test_fair_and_no_board_mean_the_base_chances(self):
        plain = mode("normal").probabilities()
        self.assertEqual(fair("normal").probabilities(0, WELL), plain)
        self.assertEqual(unfair("normal").probabilities(0), plain)

    def test_bad_settings(self):
        with self.assertRaises(ValueError):
            BoardAwareMix("classic", "nice")
        for s in (-0.1, 1.5, True, "1"):
            with self.assertRaises(ValueError):
                BoardAwareMix("classic", "unfair", s)

    def test_game_passes_the_board(self):
        seen = []

        class Spy(BoardAwareMix):
            def probabilities(self, lines=0, board=None):
                seen.append(board)
                return super().probabilities(lines, board)

        game = Game(pieces=Spy("classic", "assistive"), rng=random.Random(1))
        game.hard_drop()
        self.assertTrue(seen)
        self.assertTrue(all(isinstance(b, Board) for b in seen))
        self.assertFalse(seen[-1].is_empty())

    def test_plain_functions_still_work(self):
        game = Game(pieces=lambda rng: ExTetromino.named("O", rng=rng))
        game.hard_drop()
        self.assertEqual(game.piece.name, "O")

    def test_robot_finds_unfair_harder_than_assistive(self):
        def lines(style):
            v = Variant({"name": "t", "pieces": {"kind": "mode", "mode": "normal",
                                                 "fairness": style}})
            return playtest(v, games=2, max_pieces=80)["average_lines"]
        self.assertGreater(lines("assistive"), lines("unfair"))


class TestVariantFairness(unittest.TestCase):
    def test_round_trip_and_mix(self):
        v = Variant({"name": "Helpful", "pieces": {"kind": "mode", "mode": "easy",
                                                   "fairness": "assistive",
                                                   "strength": 0.6}})
        self.assertEqual(v.problems(), [])
        m = v.piece_mix()
        self.assertIsInstance(m, BoardAwareMix)
        self.assertEqual((m.style, m.strength), ("assistive", 0.6))
        self.assertIn("Assistive", v.describe_markdown())
        again = Variant(json.loads(v.to_json()))
        self.assertEqual(again.data["pieces"]["fairness"], "assistive")

    def test_fair_by_default(self):
        self.assertNotIsInstance(Variant().piece_mix(), BoardAwareMix)

    def test_problems(self):
        v = Variant({"name": "x", "pieces": {"kind": "mode", "mode": "easy",
                                             "fairness": "mean", "strength": 2}})
        text = " ".join(v.problems())
        self.assertIn("fairness", text)
        self.assertIn("strength", text)


if __name__ == "__main__":
    unittest.main()
