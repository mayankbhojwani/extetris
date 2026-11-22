#!/usr/bin/env python3
"""Open the ExTetris Variant Designer: design, preview, test, play and
release your own game variant without writing code.

    python3 design.py                       start with a new variant
    python3 design.py variants/classic.json open an existing variant
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from play import check_setup  # noqa: E402


def main():
    if any(a.startswith("-") for a in sys.argv[1:]):
        print(__doc__.strip())
        return
    problems = check_setup()
    if problems:
        sys.exit("Can't start the Variant Designer:\n\n" + "\n\n".join(problems))
    sys.path.insert(0, str(ROOT / "src"))
    from extetris.designer import VariantDesigner
    designer = VariantDesigner()
    if len(sys.argv) > 1:
        designer.open(sys.argv[1])
    designer.run()


if __name__ == "__main__":
    main()
