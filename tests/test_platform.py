"""Phase 8 tests: the platform layer (variants, robot, release, designer).

Run from the project root:
    python3 -B -m unittest discover -s tests -v
"""
import json
import random
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from extetris import NoHole  # noqa: E402
from extetris.playtest import autoplay, best_move, playtest, summary  # noqa: E402
from extetris.release import build_release  # noqa: E402
from extetris.variant import Variant  # noqa: E402

CLASSICS = {"I", "O", "T", "S", "Z", "L", "Γ"}


class TestVariant(unittest.TestCase):
    def test_default_variant_is_valid_and_playable(self):
        v = Variant()
        self.assertEqual(v.problems(), [])
        g = v.make_game()
        self.assertEqual((g.width, g.height, g.pieces_name), (10, 20, "progressive"))

    def test_save_and_load_round_trip(self):
        v = Variant({"name": "Round Trip", "board": {"width": 12},
                     "pieces": {"kind": "mix", "weights": {"classic": 3, "Γ": 1}}})
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "v.json"
            v.save(path)
            again = Variant.load(path)
            self.assertEqual(again.data, v.data)
            self.assertEqual(json.loads(path.read_text())["format"], "extetris-variant/1")

    def test_missing_parts_get_normal_values(self):
        v = Variant({"name": "Small", "board": {"width": 6}})
        self.assertEqual(v.data["board"], {"width": 6, "height": 20})
        self.assertEqual(v.data["speed"]["start_delay_ms"], 1000)

    def test_settings_reach_the_game(self):
        v = Variant({"name": "x", "board": {"width": 8, "height": 12},
                     "speed": {"start_delay_ms": 600, "speedup_every": 5,
                               "speedup_factor": 0.5, "min_delay_ms": 100}})
        g = v.make_game()
        self.assertEqual((g.width, g.height, g.delay_ms, g.speedup_every,
                          g.speedup_factor, g.min_delay_ms), (8, 12, 600, 5, 0.5, 100))

    def test_problems_are_plain_and_specific(self):
        cases = [
            ({"name": ""}, "name"),
            ({"board": {"width": 2}}, "width"),
            ({"board": {"height": "tall"}}, "height"),
            ({"speed": {"speedup_factor": 1.5}}, "speedup factor"),
            ({"speed": {"start_delay_ms": 100, "min_delay_ms": 500}}, "fastest"),
            ({"pieces": {"kind": "mode", "mode": "nightmare"}}, "nightmare"),
            ({"pieces": {"kind": "mix", "weights": {"Banana": 3}}}, "Banana"),
            ({"pieces": {"kind": "mix", "weights": {"classic": -1}}}, "0 or more"),
            ({"pieces": {"kind": "mix", "weights": {"classic": 0}}}, "more than 0"),
            ({"pieces": {"kind": "progressive", "every_lines": 5, "stages": []}}, "stage"),
            ({"pieces": {"kind": "progressive", "every_lines": 0,
                         "stages": ["classic"]}}, "every lines"),
            ({"pieces": {"kind": "teleport"}}, "kind"),
        ]
        for data, word in cases:
            problems = Variant(data).problems()
            self.assertTrue(problems, data)
            self.assertIn(word.lower(), " ".join(problems).lower(), data)

    def test_invalid_variant_refuses_to_make_a_game(self):
        with self.assertRaises(ValueError):
            Variant({"board": {"width": 1}}).make_game()

    def test_bad_file_gives_plain_error(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.json"
            p.write_text("{ not json")
            with self.assertRaisesRegex(ValueError, "isn't a valid variant file"):
                Variant.load(p)

    def test_piece_kinds(self):
        self.assertEqual(set(Variant({"pieces": {"kind": "mode", "mode": "classic"}})
                             .piece_mix().probabilities()), CLASSICS)
        mixed = Variant({"pieces": {"kind": "mix", "weights": {"I": 3, "O": 1}}}).piece_mix()
        self.assertEqual(mixed.probabilities(), {"I": 0.75, "O": 0.25})
        prog = Variant({"pieces": {"kind": "progressive", "every_lines": 4,
                                   "stages": ["classic", {"TwoHole": 1}]}}).piece_mix()
        self.assertEqual(set(prog.probabilities(3)), CLASSICS)
        self.assertEqual(set(prog.probabilities_by_class(4)), {"TwoHole"})

    def test_slug_and_readme(self):
        v = Variant({"name": "My Fun Game!", "author": "Me",
                     "pieces": {"kind": "progressive", "every_lines": 5,
                                "stages": ["classic", "hard"]}})
        self.assertEqual(v.slug, "my-fun-game")
        readme = v.describe_markdown()
        for text in ("# My Fun Game!", "By Me.", "From 5 lines cleared", "play.command"):
            self.assertIn(text, readme)

    def test_sample_variants_are_valid(self):
        files = sorted((ROOT / "variants").glob("*.json"))
        self.assertGreaterEqual(len(files), 3)
        for f in files:
            v = Variant.load(f)
            self.assertEqual(v.problems(), [], f.name)
            v.make_game().hard_drop()


class TestRobot(unittest.TestCase):
    def test_drop_at_follows_the_rules(self):
        g = Variant({"pieces": {"kind": "mode", "mode": "classic"}}).make_game(
            rng=random.Random(0))
        other = NoHole("O") if g.piece.name != "O" else NoHole("I")
        self.assertFalse(g.drop_at(other, 0))          # not the falling piece
        self.assertFalse(g.drop_at(g.piece, 99))        # off the board
        self.assertTrue(g.drop_at(g.piece.rotated_cw(), 0))
        self.assertEqual(g.pieces_placed, 1)

    def test_robot_clears_lines_on_classic(self):
        g = Variant({"pieces": {"kind": "mode", "mode": "classic"}}).make_game(
            rng=random.Random(1))
        autoplay(g, max_pieces=120)
        self.assertGreater(g.lines, 20)

    def test_best_move_is_legal(self):
        g = Variant().make_game(rng=random.Random(2))
        turn, col = best_move(g)
        self.assertTrue(g.board.fits(turn, 0, col))

    def test_playtest_ranks_modes_by_difficulty(self):
        def lines(mode_name):
            v = Variant({"pieces": {"kind": "mode", "mode": mode_name}})
            return playtest(v, games=3, max_pieces=150, seed=4)["average_lines"]
        self.assertGreater(lines("classic"), lines("chaos"))

    def test_playtest_is_repeatable_and_summarised(self):
        v = Variant()
        a = playtest(v, games=2, max_pieces=60, seed=9)
        b = playtest(v, games=2, max_pieces=60, seed=9)
        self.assertEqual(a, b)
        self.assertIn("Average lines cleared", summary(a))


class TestRelease(unittest.TestCase):
    def test_release_contents_and_it_runs(self):
        v = Variant({"name": "Release Me", "pieces": {"kind": "mode", "mode": "easy"}})
        with tempfile.TemporaryDirectory() as d:
            zip_path = build_release(v, d)
            self.assertEqual(zip_path.name, "release-me.zip")
            with zipfile.ZipFile(zip_path) as z:
                names = set(z.namelist())
                for must in ("play.py", "play.sh", "play.command", "play.bat",
                             "variant.json", "README.md", "extetris/game.py",
                             "extetris/window.py"):
                    self.assertIn(f"release-me/{must}", names)
                self.assertFalse(any("__pycache__" in n for n in names))
                self.assertIn(b"\r\n", z.read("release-me/play.bat"))
                mode = z.getinfo("release-me/play.command").external_attr >> 16
                self.assertTrue(mode & 0o100, "play.command must be executable")
                unpacked = Path(d) / "unpacked"
                z.extractall(unpacked)
            play = unpacked / "release-me" / "play.py"
            for flag, expect in (("--check", "Ready to play"), ("--info", "# Release Me")):
                out = subprocess.run([sys.executable, "-B", str(play), flag],
                                     capture_output=True, text=True, timeout=60)
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assertIn(expect, out.stdout)

    def test_invalid_variant_is_not_released(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "Fix these"):
                build_release(Variant({"name": ""}), d)
            self.assertEqual(list(Path(d).iterdir()), [])


class TestDesigner(unittest.TestCase):
    """Opens a hidden Variant Designer; skipped where no window can open."""

    def setUp(self):
        try:
            import tkinter as tk
            self.root = tk.Tk()
        except Exception as e:
            self.skipTest(f"no window available: {e}")
        self.root.withdraw()
        from extetris.designer import VariantDesigner
        self.d = VariantDesigner(master=self.root)

    def tearDown(self):
        self.d.dirty = False
        self.root.destroy()

    def test_starts_valid_with_a_preview(self):
        self.assertEqual(self.d.variant.problems(), [])
        self.assertEqual(set(self.d.current_probabilities), CLASSICS)
        self.assertIn("Ready", self.d.problem_box.cget("text"))

    def test_bad_value_shows_a_problem_and_recovers(self):
        self.d.v["width"].set("2")
        self.assertIn("width", self.d.problem_box.cget("text"))
        self.assertTrue(self.d.dirty)
        self.d.v["width"].set("12")
        self.assertEqual(self.d.variant.data["board"]["width"], 12)
        self.assertIn("Ready", self.d.problem_box.cget("text"))

    def test_sliders_make_a_mix(self):
        self.d.v["kind"].set("mix")
        for var in self.d.shares.values():
            var.set(0)
        self.d.shares["classic"].set(50)
        self.d.shares["TwoHole"].set(50)
        by_class = self.d.variant.piece_mix().probabilities_by_class()
        self.assertAlmostEqual(by_class["TwoHole"], 0.5)

    def test_progressive_stages_with_my_mix(self):
        self.d.v["kind"].set("progressive")
        self.d.shares["classic"].set(0)
        self.d.shares["OneHole"].set(40)
        self.d.stages[1].set("my mix")
        stages = self.d.variant.data["pieces"]["stages"]
        self.assertEqual(stages[0], "classic")
        self.assertIsInstance(stages[1], dict)

    def test_percent_faster_becomes_factor(self):
        self.d.v["faster_pct"].set("25")
        self.assertEqual(self.d.variant.data["speed"]["speedup_factor"], 0.75)

    def test_open_save_and_release(self):
        with tempfile.TemporaryDirectory() as d:
            self.d.open(str(ROOT / "variants" / "wide-board.json"))
            self.assertEqual(self.d.v["width"].get(), "14")
            self.d.v["name"].set("Wide Copy")
            self.d.path = Path(d) / "copy.json"
            self.assertTrue(self.d.save())
            self.assertEqual(Variant.load(Path(d) / "copy.json").name, "Wide Copy")
            from unittest import mock
            with mock.patch("extetris.designer.messagebox.showinfo"):
                zip_path = self.d.release(out_dir=d)
            self.assertTrue(Path(zip_path).exists())

    def test_play_opens_a_game_window(self):
        win = self.d.play()
        self.assertEqual(win.game.width, 10)
        win.root.destroy()


if __name__ == "__main__":
    unittest.main()
