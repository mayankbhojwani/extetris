"""Phase 2 tests: the piece layer, checked against the Phase 1 census.

Run from the project root:
    python3 -B -m unittest discover -s tests -v

Uses only the standard library's unittest plus numpy. The starter's
allextetrominoes.py is loaded read-only, by path, to compare against.
"""
import importlib.util
import random
import sys
import unittest
from collections import Counter
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from extetris import (DIFFICULTY_CLASSES, ExTetromino, FourHole,  # noqa: E402
                      NoHole, OneHole, PieceGenerator, Shape, SixHole,
                      ThreeHole, TwoHole)
from extetris import geometry as g  # noqa: E402


def starter_matrices():
    spec = importlib.util.spec_from_file_location(
        "_starter_allextetrominoes", ROOT / "allextetrominoes.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {i: np.array(getattr(mod, f"Extetromino{i}"), dtype=bool).copy()
            for i in range(1, 74)}


class TestGenerator(unittest.TestCase):
    def test_counts_match_phase1(self):
        gen = PieceGenerator(4, "corners")
        self.assertEqual(len(gen.shapes()), 34)
        self.assertEqual(len(gen.free_shapes()), 22)

    def test_edges_only_gives_the_7_classics(self):
        self.assertEqual(len(PieceGenerator(4, "edges").shapes()), 7)
        self.assertEqual(len(PieceGenerator(4, "edges").free_shapes()), 5)

    def test_same_pieces_as_starter_file(self):
        generated = {g.one_sided_key(m) for m in PieceGenerator().shapes()}
        starter = {g.one_sided_key(m) for m in starter_matrices().values()}
        self.assertEqual(generated, starter)

    def test_order_is_stable(self):
        a = [g.key(m) for m in PieceGenerator().shapes()]
        b = [g.key(m) for m in PieceGenerator().shapes()]
        self.assertEqual(a, b)

    def test_known_counts_for_other_sizes(self):
        # Well-known counts: 18 one-sided and 12 free pentominoes (5 squares).
        self.assertEqual(len(PieceGenerator(5, "edges").shapes()), 18)
        self.assertEqual(len(PieceGenerator(5, "edges").free_shapes()), 12)

    def test_bad_arguments(self):
        with self.assertRaises(ValueError):
            PieceGenerator(4, "diagonal")
        with self.assertRaises(ValueError):
            PieceGenerator(0)


class TestShapeIsImmutable(unittest.TestCase):
    """The starter's bugs B1-B3 must be impossible now."""

    def test_rotation_returns_new_object_and_leaves_original(self):
        piece = ExTetromino.named("L", rng=random.Random(0))
        before = piece.matrix.copy()
        turned = piece.rotated_cw()
        self.assertIsNot(turned, piece)
        self.assertTrue(np.array_equal(piece.matrix, before))
        self.assertFalse(np.array_equal(turned.matrix, before))

    def test_matrix_cannot_be_written(self):
        piece = NoHole("T")
        with self.assertRaises(ValueError):
            piece.matrix[0, 0] = not piece.matrix[0, 0]

    def test_input_array_is_copied(self):
        source = np.array([[True, True], [True, True]])
        s = Shape(source)
        source[0, 0] = False
        self.assertTrue(s.matrix.all())

    def test_catalogue_survives_rotations(self):
        before = [g.key(i.standard_turn) for i in ExTetromino.catalogue()]
        p = NoHole("L")
        for _ in range(7):
            p = p.rotated_ccw()
        after = [g.key(i.standard_turn) for i in ExTetromino.catalogue()]
        self.assertEqual(before, after)

    def test_four_turns_return_to_start(self):
        for info in ExTetromino.catalogue():
            p = info.piece_class(info.name, rng=random.Random(1))
            q = p.rotated_cw().rotated_cw().rotated_cw().rotated_cw()
            self.assertEqual(p, q, info.name)
            self.assertEqual(p.rotated_cw().rotated_ccw(), p, info.name)

    def test_rotation_never_mirrors(self):
        for info in ExTetromino.catalogue():
            p = info.piece_class(info.name)
            for _ in range(4):
                p = p.rotated_cw()
                self.assertEqual(g.one_sided_key(p.matrix),
                                 g.one_sided_key(info.standard_turn), info.name)

    def test_rotated_piece_keeps_class_and_name(self):
        p = TwoHole("TwoHole-04").rotated_cw()
        self.assertIsInstance(p, TwoHole)
        self.assertEqual(p.name, "TwoHole-04")


class TestDifficultyClasses(unittest.TestCase):
    def test_class_sizes(self):
        sizes = {c.__name__: len(c.catalogue()) for c in DIFFICULTY_CLASSES}
        self.assertEqual(sizes, {"NoHole": 5, "OneHole": 10, "TwoHole": 11,
                                 "ThreeHole": 3, "FourHole": 4, "SixHole": 1})
        self.assertEqual(len(ExTetromino.catalogue()), 34)

    def test_every_piece_in_exactly_one_class(self):
        names = [i.name for i in ExTetromino.catalogue()]
        self.assertEqual(len(names), len(set(names)))

    def test_spawned_piece_has_its_class_hole_count(self):
        rng = random.Random(42)
        for cls in DIFFICULTY_CLASSES:
            for _ in range(50):
                p = cls(rng=rng)
                self.assertIsInstance(p, cls)
                self.assertEqual(p.holes, cls.SPAWN_HOLES, p.name)

    def test_spawn_turn_is_flattest(self):
        for info in ExTetromino.catalogue():
            lowest = min(t.shape[0] for t in g.rotations(info.standard_turn))
            for turn in info.spawn_turns:
                self.assertEqual(turn.shape[0], lowest, info.name)

    def test_ties_are_picked_at_random(self):
        tied = [i for i in ExTetromino.catalogue() if len(i.spawn_turns) > 1]
        self.assertEqual(len(tied), 13)  # matches the Phase 2 check
        info = tied[0]
        rng = random.Random(7)
        seen = Counter(g.key(info.piece_class(info.name, rng=rng).matrix)
                       for _ in range(200))
        self.assertEqual(set(seen), {g.key(t) for t in info.spawn_turns})

    def test_same_seed_same_pieces(self):
        a = [TwoHole(rng=random.Random(3)).name for _ in range(5)]
        b = [TwoHole(rng=random.Random(3)).name for _ in range(5)]
        self.assertEqual(a, b)

    def test_base_class_cannot_be_made_directly(self):
        with self.assertRaises(TypeError):
            ExTetromino()

    def test_wrong_class_for_name_explains_itself(self):
        with self.assertRaisesRegex(ValueError, "NoHole"):
            TwoHole("T")
        with self.assertRaises(ValueError):
            NoHole("nonsense")
        with self.assertRaises(ValueError):
            NoHole(99)

    def test_lookup_by_number(self):
        self.assertEqual(OneHole(3).name, "OneHole-01")
        self.assertEqual(TwoHole(3).name, "TwoHole-03")

    def test_classes_are_disjoint_and_complete(self):
        all_classes = {NoHole, OneHole, TwoHole, ThreeHole, FourHole, SixHole}
        self.assertEqual(set(DIFFICULTY_CLASSES), all_classes)
        self.assertEqual({i.piece_class for i in ExTetromino.catalogue()}, all_classes)


class TestConstructors(unittest.TestCase):
    """Each difficulty class overrides the constructor (Phase 2 decision)."""

    def test_each_class_defines_its_own_constructor(self):
        for cls in DIFFICULTY_CLASSES:
            self.assertIn("__init__", vars(cls), cls.__name__)
            self.assertTrue(cls.__init__.__doc__, cls.__name__)

    def test_overrides_still_reach_the_shared_work(self):
        for cls in DIFFICULTY_CLASSES:
            p = cls(1, rng=random.Random(0))
            self.assertIsInstance(p, cls)
            self.assertEqual(p.name, cls.catalogue()[0].name)

    def test_wrong_class_suggests_the_right_one(self):
        with self.assertRaisesRegex(ValueError, r"use OneHole\('S'\)"):
            NoHole("S")

    def test_sixhole_explains_there_is_only_one(self):
        with self.assertRaisesRegex(ValueError, "only one six-hole piece"):
            SixHole(2)
        self.assertEqual(SixHole("SixHole-01").name, "SixHole-01")
        with self.assertRaisesRegex(ValueError, r"use NoHole\('T'\)"):
            SixHole("T")


class TestNames(unittest.TestCase):
    def test_classic_names_match_starter_comments(self):
        # Starter comments: 1 I, 2 O, 3 L, 4 T, 5 Gamma, 6 S, 7 Z
        starter = starter_matrices()
        expected = {1: "I", 2: "O", 3: "L", 4: "T", 5: "Γ", 6: "S", 7: "Z"}
        for idx, name in expected.items():
            p = ExTetromino.named(name)
            self.assertTrue(p.same_piece_as(Shape(starter[idx])),
                            f"{name} should match starter #{idx}")

    def test_aliases(self):
        self.assertEqual(ExTetromino.named("Gamma").name, "Γ")
        self.assertEqual(ExTetromino.named("J").name, "Γ")

    def test_classics_are_in_expected_classes(self):
        for name in "IOLTΓ":
            self.assertIsInstance(ExTetromino.named(name), NoHole)
        for name in "SZ":
            self.assertIsInstance(ExTetromino.named(name), OneHole)

    def test_auto_names_are_numbered_per_class(self):
        for cls in DIFFICULTY_CLASSES:
            auto = [i.name for i in cls.catalogue() if "-" in i.name]
            want = [f"{cls.__name__}-{n:02d}" for n in range(1, len(auto) + 1)]
            self.assertEqual(auto, want)

    def test_labels(self):
        p = SixHole()
        self.assertEqual((p.box_size, p.touching, p.is_chiral), ("4x4", "corners", False))
        p = NoHole("I")
        self.assertEqual((p.box_size, p.touching), ("4x1", "edges"))


if __name__ == "__main__":
    unittest.main()
