# ExTetris

Extended Tetris: pieces of 4 squares that may touch **at their corners**, not
only along their sides. That gives 34 pieces instead of the classic 7. The
engine lets a game designer choose which pieces appear and how often, without
being a programmer.

Assignment for CS F301 Principles of Programming Languages, Sem-I 2026-27.
It is built on, and replaces, the starter code by Ramprasad S. Joshi, which is
kept unchanged in this folder as the reference.

## Play

| system | how |
|---|---|
| macOS | double-click `play.command`, or run `./play.sh` |
| Windows | double-click `play.bat` |
| Linux | `./play.sh` |
| any | `python3 play.py` |

Needs Python 3.9+ with numpy and tkinter. Choose a piece mode with
`--mode classic | easy | normal | hard | chaos | progressive`, for example
`./play.sh --mode easy`.

Keys: ← → move, ↑ turn, Z turn back, ↓ down, Space drop, P pause.

## Documentation

| document | for |
|---|---|
| [Game Programmer's Manual](docs/manual.md) | making your own game variant (start here) |
| [Design document](docs/design.md) | how the engine is built, with UML diagrams |
| [API reference](docs/api.md) | every class and function (generated from the code) |
| [Phase 1 analysis](docs/analysis.md) | the starter's 73 shapes and its bugs |
| [AI usage report](docs/ai_usage_report.md) | how AI was used, phase by phase, and effort compared with no AI |
| [AI interaction log](docs/ai_log/raw_log.md) | every AI prompt and response, as the assignment requires |

## Folder layout

```text
play.py, play.sh, play.command, play.bat   start the game
Makefile                                    shortcuts: make play / test / docs
src/extetris/      the new engine
examples/          three small game variants to copy
tests/             automatic tests (python3 -B -m unittest discover -s tests)
tools/             shape_census.py (Phase 1), make_api_docs.py (API reference)
docs/              the documents above
engine.py, board.py, shape.py, allextetrominoes.py
                   the original starter code, unchanged (run: python3 engine.py)
```

## For developers

```bash
make test        # run the 99+ automatic tests
make docs        # regenerate docs/api.md and the Phase 1 census
make catalogue   # list every piece by class
```

## Licence

The starter code is GPL-3.0 (see the headers in `engine.py` and the other
starter files). This derived work is distributed under the same licence.
