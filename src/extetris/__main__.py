"""Start ExTetris.

    python3 -m extetris                  play (needs PYTHONPATH=src)
    python3 -m extetris --mode easy      play with a chosen piece mode:
                                         classic, easy, normal, hard, chaos,
                                         progressive (the default)
    python3 -m extetris --catalogue      list every piece by difficulty class
"""
import sys


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--catalogue" in argv:
        from .catalogue import main as show_catalogue
        show_catalogue()
        return
    pieces = "progressive"
    if "--mode" in argv:
        i = argv.index("--mode")
        if i + 1 >= len(argv):
            sys.exit("--mode needs a name: classic, easy, normal, hard, chaos or progressive")
        pieces = argv[i + 1]
    from .game import Game
    from .mixes import mode
    try:
        mode(pieces)
    except ValueError as e:
        sys.exit(str(e))
    from .window import GameWindow
    GameWindow(Game(pieces=pieces)).run()


if __name__ == "__main__":
    main()
