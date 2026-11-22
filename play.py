#!/usr/bin/env python3
"""Play ExTetris:            python3 play.py
Choose the piece mode:      python3 play.py --mode easy
                            (classic, easy, normal, hard, chaos, progressive)
List all the pieces:        python3 play.py --catalogue
Check your setup:           python3 play.py --check
Play a saved variant:       python3 play.py --variant variants/gentle-start.json
Release a variant as a zip: python3 play.py --release variants/gentle-start.json
(To design a variant without code, use design.py / design.command / design.bat.)

Needs Python 3.9+ with numpy and tkinter. (The original starter game is still
available as `python3 engine.py`.)
"""
import sys
from pathlib import Path

HELP_NUMPY = ("numpy is missing. Install it with:\n"
              "    python3 -m pip install numpy\n"
              "(on Windows:  py -m pip install numpy)")
HELP_TK = ("tkinter is missing.\n"
           "  macOS / Windows: install Python from https://www.python.org\n"
           "  Linux (Debian/Ubuntu): sudo apt install python3-tk")


def check_setup(need_window=True):
    """Return a list of problems (empty if everything is ready)."""
    problems = []
    if sys.version_info < (3, 9):
        problems.append(f"Python 3.9 or newer is needed; this is {sys.version.split()[0]}.")
    try:
        import numpy  # noqa: F401
    except ImportError:
        problems.append(HELP_NUMPY)
    if need_window:
        try:
            import tkinter  # noqa: F401
        except ImportError:
            problems.append(HELP_TK)
    return problems


def main():
    args = sys.argv[1:]
    problems = check_setup(need_window="--catalogue" not in args)
    if "--check" in args:
        if problems:
            print("Not ready:\n\n" + "\n\n".join(problems))
            sys.exit(1)
        import numpy
        import tkinter
        print(f"Ready to play.\n  Python  {sys.version.split()[0]}\n"
              f"  numpy   {numpy.__version__}\n  Tk      {tkinter.TkVersion}")
        return
    if problems:
        sys.exit("Can't start ExTetris:\n\n" + "\n\n".join(problems))
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    for flag in ("--variant", "--release"):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                sys.exit(f"{flag} needs a variant file, e.g. {flag} variants/classic.json")
            from extetris.variant import Variant
            try:
                variant = Variant.load(args[i + 1])
                if flag == "--release":
                    from extetris.release import build_release
                    print(f"Released: {build_release(variant, root / 'releases')}")
                    return
                game = variant.make_game()
            except (OSError, ValueError) as e:
                sys.exit(str(e))
            from extetris.window import GameWindow
            GameWindow(game, title=variant.name,
                       cell_size=variant.data["window"]["cell_size"]).run()
            return
    from extetris.__main__ import main as run
    run(args)


if __name__ == "__main__":
    main()
