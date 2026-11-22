"""Start ExTetris.

    python3 -m extetris               play (needs PYTHONPATH=src)
    python3 -m extetris --catalogue   list every piece by difficulty class
"""
import sys


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--catalogue" in argv:
        from .catalogue import main as show_catalogue
        show_catalogue()
        return
    from .window import GameWindow
    GameWindow().run()


if __name__ == "__main__":
    main()
