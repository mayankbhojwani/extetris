"""Release: package a variant as a ready-to-share game.

    build_release(variant, out_dir) -> path of the .zip

The zip unpacks to one folder holding:
    play.command / play.bat / play.sh   double-click (or run) to play
    play.py                             the starter script they all call
    variant.json                        the variant itself
    README.md                           generated description of the variant
    extetris/                           a copy of the engine
Anyone with Python 3.9+, numpy and tkinter can play it; nothing else is needed.
"""
import shutil
import zipfile
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent

PLAY_PY = '''#!/usr/bin/env python3
"""Play this ExTetris variant.

    python3 play.py            play
    python3 play.py --check    check that Python, numpy and tkinter are ready
    python3 play.py --info     show the variant's settings
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def problems(need_window=True):
    out = []
    if sys.version_info < (3, 9):
        out.append("Python 3.9 or newer is needed; this is %s." % sys.version.split()[0])
    try:
        import numpy  # noqa: F401
    except ImportError:
        out.append("numpy is missing. Install it with:\\n"
                   "    python3 -m pip install numpy\\n"
                   "(on Windows:  py -m pip install numpy)")
    if need_window:
        try:
            import tkinter  # noqa: F401
        except ImportError:
            out.append("tkinter is missing.\\n"
                       "  macOS / Windows: install Python from https://www.python.org\\n"
                       "  Linux (Debian/Ubuntu): sudo apt install python3-tk")
    return out


def main():
    args = sys.argv[1:]
    found = problems(need_window="--info" not in args)
    if "--check" in args:
        print("Not ready:\\n\\n" + "\\n\\n".join(found) if found else "Ready to play.")
        sys.exit(1 if found else 0)
    if found:
        sys.exit("Can't start the game:\\n\\n" + "\\n\\n".join(found))
    sys.path.insert(0, str(HERE))
    from extetris.variant import Variant
    try:
        variant = Variant.load(HERE / "variant.json")
        game = variant.make_game()
    except ValueError as e:
        sys.exit(str(e))
    if "--info" in args:
        print(variant.describe_markdown())
        return
    from extetris.window import GameWindow
    GameWindow(game, title=variant.name,
               cell_size=variant.data["window"]["cell_size"]).run()


if __name__ == "__main__":
    main()
'''

PLAY_SH = '''#!/bin/sh
# Play this ExTetris variant (macOS / Linux).
cd "$(dirname "$0")" || exit 1
for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
        exec "$py" play.py "$@"
    fi
done
echo "Python 3.9 or newer was not found. Install it from https://www.python.org" >&2
exit 1
'''

PLAY_COMMAND = '''#!/bin/sh
# macOS: double-click to play. (First time: right-click, Open, Open.)
cd "$(dirname "$0")" || exit 1
./play.sh "$@"
status=$?
if [ $status -ne 0 ]; then
    echo
    echo "The game stopped with a problem (see above). Press Enter to close."
    read -r _
fi
exit $status
'''

PLAY_BAT = "\r\n".join([
    "@echo off",
    "rem Windows: double-click to play this ExTetris variant.",
    'cd /d "%~dp0"',
    "where py >nul 2>nul",
    "if %errorlevel%==0 (",
    "    py -3 play.py %*",
    ") else (",
    "    python play.py %*",
    ")",
    "if errorlevel 1 (",
    "    echo.",
    "    echo The game stopped with a problem, see above. If Python is missing,",
    '    echo install it from https://www.python.org and tick "Add python.exe to PATH".',
    "    pause",
    ")",
]) + "\r\n"


def _write(path, text, executable=False, newline=None):
    with open(path, "w", encoding="utf-8", newline=newline) as f:
        f.write(text)
    if executable:
        path.chmod(0o755)


def build_release(variant, out_dir):
    """Package `variant` into out_dir/<slug>/ and out_dir/<slug>.zip.

    Raises ValueError (listing the problems) if the variant isn't valid.
    Any earlier release of the same name in out_dir is replaced.
    Returns the path of the zip file.
    """
    problems = variant.problems()
    if problems:
        raise ValueError("Fix these before releasing:\n- " + "\n- ".join(problems))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    folder = out_dir / variant.slug
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir()

    shutil.copytree(ENGINE_DIR, folder / "extetris",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    variant.save(folder / "variant.json")
    _write(folder / "README.md", variant.describe_markdown())
    _write(folder / "play.py", PLAY_PY, executable=True)
    _write(folder / "play.sh", PLAY_SH, executable=True, newline="\n")
    _write(folder / "play.command", PLAY_COMMAND, executable=True, newline="\n")
    _write(folder / "play.bat", PLAY_BAT, newline="")

    zip_path = out_dir / f"{variant.slug}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(folder.rglob("*")):
            arcname = path.relative_to(out_dir).as_posix()
            info = zipfile.ZipInfo.from_file(path, arcname)
            if path.is_file():
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, path.read_bytes())   # keeps the run permissions
    return zip_path
