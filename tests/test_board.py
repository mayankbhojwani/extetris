"""Phase 3 tests: the Board.

Run from the project root:
    python3 -B -m unittest discover -s tests -v
"""
import random
import sys
import unittest
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from extetris import Board, ExTetromino, NoHole, SixHole  # noqa: E402


class TestMakingBoards(unittest.TestCase):
    def test_default_size_is_10_by_20_and_empty(self):
        b = Board()
        self.assertEqual((b.width, b.height), (10, 20))
        self.assertEqual(b.cells.shape, (20, 10))
        self.assertTrue(b.is_empty())

    def test_custom_size(self):
        b = Board(width=6, height=12)
        self.assertEqual(b.cells.shape, (12, 6))

    def test_too_small_or_wrong_type_is_rejected(self):
        with self.assertRaises(ValueError):
            Board(width=3)
        with self.assertRaises(ValueError):
            Board(height=2)
        with self.assertRaises(TypeError):
            Board(width=10.5)

    def test_cells_must_match_size(self):
        with self.assertRaises(ValueError):
            Board(4, 4, cells=np.zeros((5, 4), dtype=bool))

    def test_from_text_and_back(self):
        text = "....\n#..#\n####\n.##."
        b = Board.from_text(text)
        self.assertEqual((b.width, b.height), (4, 4))
        self.assertEqual(str(b), text.replace("#", "█").replace(".", "·"))
        self.assertEqual(Board.from_text(str(b)), b)

    def test_from_text_rejects_ragged_or_unknown(self):
        with self.assertRaises(ValueError):
            Board.from_text("....\n...")
        with self.assertRaises(ValueError):
            Board.from_text("..x.\n....")


class TestBoardIsImmutable(unittest.TestCase):
    def test_cells_cannot_be_written(self):
        with self.assertRaises(ValueError):
            Board().cells[0, 0] = True

    def test_place_returns_new_board_and_leaves_old(self):
        b = Board()
        after = b.place(NoHole("O"), 18, 0)
        self.assertTrue(b.is_empty())
        self.assertFalse(after.is_empty())
        self.assertIsNot(after, b)

    def test_clear_returns_new_board_and_leaves_old(self):
        b = Board.from_text("....\n....\n####\n#...")
        cleared, n = b.clear_full_rows()
        self.assertEqual(n, 1)
        self.assertEqual(b.full_rows(), (2,))


class TestFits(unittest.TestCase):
    def setUp(self):
        self.board = Board()            # 10 wide, 20 tall
        self.bar = NoHole("I")          # spawns lying flat: 1 x 4

    def test_inside_empty_board(self):
        self.assertTrue(self.board.fits(self.bar, 0, 0))
        self.assertTrue(self.board.fits(self.bar, 19, 6))

    def test_off_the_left_edge_does_not_wrap(self):
        # Starter bug B4: column -1 used to wrap round to the right side.
        self.assertFalse(self.board.fits(self.bar, 0, -1))

    def test_off_the_top_does_not_wrap(self):
        self.assertFalse(self.board.fits(self.bar, -1, 0))

    def test_off_the_right_and_bottom(self):
        self.assertFalse(self.board.fits(self.bar, 0, 7))
        self.assertFalse(self.board.fits(self.bar, 20, 0))

    def test_overlap_with_filled_square(self):
        b = Board.from_text("....\n....\n....\n..#.")
        o = NoHole("O")
        self.assertFalse(b.fits(o, 2, 1))
        self.assertTrue(b.fits(o, 2, 0))

    def test_piece_with_gaps_can_straddle_filled_square(self):
        # Corner-touching pieces have empty squares inside their box; a filled
        # square there is not a collision.
        diagonal = SixHole(rng=random.Random(0))
        b = Board(4, 4)
        gap = tuple(int(i) for i in np.argwhere(~diagonal.matrix)[0])
        b = b.place(np.ones((1, 1), dtype=bool), *gap)
        self.assertTrue(b.fits(diagonal, 0, 0))

    def test_place_where_it_does_not_fit_raises(self):
        with self.assertRaises(ValueError):
            self.board.place(self.bar, 0, -1)


class TestDropping(unittest.TestCase):
    def test_drop_on_empty_board_reaches_floor(self):
        b = Board()
        for info in ExTetromino.catalogue():
            p = info.piece_class(info.name, rng=random.Random(0))
            self.assertEqual(b.drop_row(p, 0), b.height - p.height, info.name)

    def test_drop_onto_stack(self):
        b = Board.from_text("....\n....\n....\n....\n.##.\n####")
        self.assertEqual(b.drop_row(NoHole("O"), 1), 2)
        self.assertEqual(b.drop_row(NoHole("O"), 0), 2)

    def test_drop_when_blocked_at_start(self):
        b = Board.from_text("#...\n....\n....\n....")
        self.assertIsNone(b.drop_row(NoHole("O"), 0))


class TestClearingRows(unittest.TestCase):
    def test_non_adjacent_full_rows(self):
        # Same case that was checked by hand on the starter in Phase 1.
        b = Board.from_text("""
            ....
            ....
            ...#
            ####
            #...
            ####
        """)
        self.assertEqual(b.full_rows(), (3, 5))
        cleared, n = b.clear_full_rows()
        self.assertEqual(n, 2)
        self.assertEqual(cleared, Board.from_text("""
            ....
            ....
            ....
            ....
            ...#
            #...
        """))

    def test_adjacent_full_rows(self):
        b = Board.from_text("....\n.#..\n####\n####")
        cleared, n = b.clear_full_rows()
        self.assertEqual(n, 2)
        self.assertEqual(cleared, Board.from_text("....\n....\n....\n.#.."))

    def test_nothing_to_clear(self):
        b = Board.from_text("....\n....\n....\n###.")
        same, n = b.clear_full_rows()
        self.assertEqual((n, same), (0, b))


class TestHoles(unittest.TestCase):
    def test_simple_board(self):
        b = Board.from_text("....\n#...\n.#..\n....")
        self.assertEqual(b.holes(), 3)   # 2 under the left '#', 1 under the next

    def test_matches_piece_hole_counts_on_a_flat_floor(self):
        # Cross-check of Phase 1/2: every turn of every piece, dropped on an
        # empty board, leaves exactly piece.holes holes.
        for info in ExTetromino.catalogue():
            p = info.piece_class(info.name, rng=random.Random(0))
            for _ in range(4):
                b = Board()
                row = b.drop_row(p, 0)
                self.assertEqual(b.place(p, row, 0).holes(), p.holes, info.name)
                p = p.rotated_cw()


class TestRender(unittest.TestCase):
    def test_falling_piece_is_drawn_but_not_placed(self):
        b = Board(4, 4)
        picture = b.render(NoHole("O"), 2, 1)
        self.assertEqual(picture, "····\n····\n·▒▒·\n·▒▒·")
        self.assertTrue(b.is_empty())

    def test_rows_have_equal_width(self):
        # Starter bug B10: filled and empty squares had different widths.
        b = Board().place(NoHole("I"), 19, 0)
        widths = {len(line) for line in str(b).splitlines()}
        self.assertEqual(widths, {10})


if __name__ == "__main__":
    unittest.main()
