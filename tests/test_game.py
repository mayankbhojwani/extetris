"""Phase 4 tests: the Game rules (no window) and a quick window check.

Run from the project root:
    python3 -B -m unittest discover -s tests -v
"""
import random
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from extetris import Board, Game, NoHole  # noqa: E402


def always(name):
    """A piece source that always gives the same named piece."""
    return lambda rng: NoHole(name, rng=rng)


class TestStarting(unittest.TestCase):
    def test_new_game_spawns_centred_at_top(self):
        g = Game(pieces=always("O"))
        self.assertEqual((g.row, g.col), (0, 4))   # (10 - 2) // 2
        self.assertIsNotNone(g.next_piece)
        self.assertFalse(g.game_over or g.paused)
        self.assertEqual((g.lines, g.pieces_placed, g.delay_ms), (0, 0, 1000))

    def test_piece_source_must_give_a_piece(self):
        with self.assertRaises(TypeError):
            Game(pieces=lambda rng: "not a piece")

    def test_bad_speed_settings(self):
        with self.assertRaises(ValueError):
            Game(speedup_factor=1.5)
        with self.assertRaises(ValueError):
            Game(speedup_every=0)


class TestMoving(unittest.TestCase):
    def test_left_stops_at_the_wall(self):
        # Starter bug B4 at game level: the piece must not leave the board.
        g = Game(pieces=always("O"))
        while g.move_left():
            pass
        self.assertEqual(g.col, 0)
        self.assertFalse(g.move_left())

    def test_right_stops_at_the_wall(self):
        g = Game(pieces=always("O"))
        while g.move_right():
            pass
        self.assertEqual(g.col, 8)

    def test_turning_next_to_the_right_wall_kicks_inwards(self):
        g = Game(pieces=always("I"))
        self.assertTrue(g.rotate_cw())            # now standing up
        while g.move_right():
            pass
        self.assertEqual(g.col, 9)
        self.assertTrue(g.rotate_cw())            # lying down again
        self.assertTrue(g.board.fits(g.piece, g.row, g.col))
        self.assertEqual(g.col + g.piece.width, 10)

    def test_four_turns_return_to_same_shape(self):
        g = Game(pieces=always("T"))
        start = g.piece
        for _ in range(4):
            g.rotate_ccw()
        self.assertEqual(g.piece, start)


class TestDroppingAndLocking(unittest.TestCase):
    def test_hard_drop_locks_immediately(self):
        # Starter limitation L3: Space used to wait for the next gravity tick.
        g = Game(pieces=always("O"))
        g.hard_drop()
        self.assertEqual(g.pieces_placed, 1)
        self.assertEqual(int(g.board.cells.sum()), 4)
        self.assertEqual(g.row, 0)               # new piece back at the top

    def test_tick_falls_then_locks(self):
        g = Game(width=4, height=4, pieces=always("O"))
        self.assertTrue(g.tick())
        self.assertEqual(g.row, 1)
        g.tick()                                  # reaches the floor (row 2)
        g.tick()                                  # can't fall: locks
        self.assertEqual(g.pieces_placed, 1)

    def test_soft_drop_is_one_tick(self):
        g = Game(pieces=always("O"))
        g.soft_drop()
        self.assertEqual(g.row, 1)

    def test_clearing_lines_counts_them(self):
        g = Game(width=4, height=6, pieces=always("O"))
        g.board = Board.from_text("....\n....\n....\n....\n#..#\n#..#")
        g.hard_drop()                             # O fills the middle gap
        self.assertEqual(g.lines, 2)
        self.assertTrue(g.board.is_empty())


class TestSpeed(unittest.TestCase):
    def test_speed_up_when_a_multi_line_clear_jumps_past_100(self):
        # Starter bug B8: 99 -> 101 lines never triggered a speed-up.
        g = Game(width=4, height=6, pieces=always("O"))
        g.board = Board.from_text("....\n....\n....\n....\n#..#\n#..#")
        g.lines = 99
        g.hard_drop()
        self.assertEqual(g.lines, 101)
        self.assertEqual(g.delay_ms, 900)

    def test_menu_speed_controls_and_floor(self):
        g = Game(min_delay_ms=500)
        g.speed_up()
        self.assertEqual(g.delay_ms, 900)
        g.slow_down()
        self.assertEqual(g.delay_ms, 1000)
        g.speed_up(times=50)
        self.assertEqual(g.delay_ms, 500)


class TestPauseAndGameOver(unittest.TestCase):
    def test_pause_blocks_every_move(self):
        g = Game(pieces=always("T"))
        g.toggle_pause()
        before = (g.row, g.col, g.piece)
        for move in (g.move_left, g.move_right, g.rotate_cw, g.rotate_ccw,
                     g.soft_drop, g.hard_drop, g.tick):
            self.assertFalse(move())
        self.assertEqual((g.row, g.col, g.piece), before)
        g.toggle_pause()
        self.assertTrue(g.move_left())

    def test_game_over_when_new_piece_cannot_fit(self):
        g = Game(width=4, height=4, pieces=always("O"))
        g.board = Board.from_text("....\n....\n.#..\n#.##")
        g.hard_drop()                             # lands on top; next can't fit
        self.assertTrue(g.game_over)
        self.assertFalse(g.move_left())
        g.toggle_pause()                          # pausing is ignored once over
        self.assertFalse(g.paused)
        self.assertIn("█", g.render())

    def test_new_game_after_game_over(self):
        # Starter bug B7: game_over_status was never set, so this never worked.
        g = Game(width=4, height=4, pieces=always("O"))
        g.board = Board.from_text("....\n....\n.#..\n#.##")
        g.hard_drop()
        g.new_game()
        self.assertFalse(g.game_over)
        self.assertTrue(g.board.is_empty())
        self.assertEqual(g.lines, 0)


class TestLongRandomPlay(unittest.TestCase):
    def play(self, seed, steps=3000):
        g = Game(rng=random.Random(seed))
        moves = [g.move_left, g.move_right, g.rotate_cw, g.rotate_ccw,
                 g.soft_drop, g.tick, g.hard_drop]
        pick = random.Random(seed + 1)
        for _ in range(steps):
            if g.game_over:
                g.new_game()
            pick.choice(moves)()
            if not g.game_over:
                self.assertTrue(g.board.fits(g.piece, g.row, g.col))
            self.assertEqual(g.board.full_rows(), ())
        return g

    def test_piece_always_on_board_and_no_full_rows_left(self):
        for seed in range(3):
            self.play(seed)

    def test_same_seed_same_game(self):
        a, b = self.play(11, 800), self.play(11, 800)
        self.assertEqual(a.board, b.board)
        self.assertEqual((a.lines, a.pieces_placed), (b.lines, b.pieces_placed))


class TestWindow(unittest.TestCase):
    """Opens a hidden window briefly; skipped where tkinter can't open one."""

    def setUp(self):
        try:
            import tkinter as tk
            self.root = tk.Tk()
        except Exception as e:  # no display, or no tkinter
            self.skipTest(f"no window available: {e}")
        self.root.withdraw()
        from extetris.window import GameWindow
        self.win = GameWindow(Game(pieces=always("T")), master=self.root)

    def tearDown(self):
        self.root.destroy()

    def pending_timers(self):
        return len(self.root.tk.splitlist(self.root.tk.call("after", "info")))

    def test_only_one_gravity_timer_even_after_keys_while_paused(self):
        # Starter bug B6: Down while paused started extra timers.
        self.win._do(self.win.game.toggle_pause)
        for _ in range(5):
            self.win._do(self.win.game.soft_drop)
        self.win._gravity()
        self.win.new_game()
        self.assertEqual(self.pending_timers(), 1)

    def test_keys_change_the_game(self):
        col = self.win.game.col
        self.win._do(self.win.game.move_left)
        self.assertLess(self.win.game.col, col)
        self.win._do(self.win.game.hard_drop)
        self.assertEqual(self.win.game.pieces_placed, 1)
        self.assertIn("Lines: 0", self.win.status.get())


if __name__ == "__main__":
    unittest.main()
