#!/usr/bin/env python3
"""Play ExTetris:            python3 play.py
Choose the piece mode:      python3 play.py --mode easy
                            (classic, easy, normal, hard, chaos, progressive)
List all the pieces:        python3 play.py --catalogue

Needs Python 3 with numpy and tkinter. (The original starter game is still
available as `python3 engine.py`.)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from extetris.__main__ import main  # noqa: E402

if __name__ == "__main__":
    main()
