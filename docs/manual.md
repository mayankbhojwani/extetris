# Game Programmer's Manual

This manual is for **game designers**: people who want to make their own
version of ExTetris without being programmers. You design a variant in the
**Variant Designer** window (section 4): pick settings, watch a live
preview, play it, let a robot playtest it, and release it as a zip anyone
can double-click. No code is needed. Programmers can also use ExTetris as a
Python library (sections 5–7).

If you want every detail of every class, see the [API reference](api.md).
For how the engine is built, see the [design document](design.md).

---

## 1. What you need

- **Python 3** (3.9 or newer) with **numpy** and **tkinter**.
  - **macOS / Windows:** the installer from python.org includes tkinter. Add
    numpy with `python3 -m pip install numpy` (on Windows, `py -m pip install numpy`).
  - **Linux:** you may also need your system's tkinter package, e.g.
    `sudo apt install python3-tk`.
- Nothing else.

If something is missing, the game tells you what to install when you start it.

## 2. Playing

| how | command |
|---|---|
| **Double-click** (macOS) | `play.command` |
| **Double-click** (Windows) | `play.bat` |
| From a terminal (macOS / Linux) | `./play.sh` |
| From a terminal (any system) | `python3 play.py` |

You can add a mode when starting from a terminal: `./play.sh --mode easy`,
`play.bat --mode chaos` or `python3 play.py --mode classic`.

### Keys

| key | action |
|---|---|
| ← / → | move |
| ↑ | turn clockwise |
| Z | turn anticlockwise |
| ↓ | down one row |
| Space | drop to the bottom and lock |
| P | pause / resume |

### Menus

- **Game:** New Game, Pause / Resume, Speed Up, Slow Down, Save Board as
  Text, Quit.
- **Pieces:** choose a piece mode (see section 3). The change applies from the
  piece after the "Next" one.
- **Help:** the list of keys, and About.

The **colour** of the falling piece shows how awkward it is:

| colour | class | holes it leaves when it first appears |
|---|---|---|
| green | NoHole | 0 |
| blue | OneHole | 1 |
| purple | TwoHole | 2 |
| orange | ThreeHole | 3 |
| red | FourHole | 4 |
| black | SixHole | 6 |

## 3. The pieces and the modes

Every piece has 4 squares. In normal Tetris the squares must share sides. In
ExTetris they may also touch **only at a corner**, which gives 34 pieces
instead of 7.

To see all of them, with their names, run:

```bash
python3 play.py --catalogue
```

Pieces are grouped by **how many holes they leave** when they land on a flat
floor (a hole is an empty square trapped under the piece):

| class | pieces | names |
|---|---|---|
| NoHole | 5 | I, O, L, T, Γ |
| OneHole | 10 | S, Z, OneHole-01 … OneHole-08 |
| TwoHole | 11 | TwoHole-01 … TwoHole-11 |
| ThreeHole | 3 | ThreeHole-01 … ThreeHole-03 |
| FourHole | 4 | FourHole-01 … FourHole-04 |
| SixHole | 1 | SixHole-01 (the long diagonal) |

"Gamma" and "J" also work as names for Γ.

### Ready-made modes

| mode | what you get |
|---|---|
| `classic` | only I, O, T, S, Z, L, Γ |
| `easy` | 85 % classic pieces, 15 % one-hole pieces |
| `normal` | mostly classic, some harder pieces, rarely the diagonal |
| `hard` | a quarter classic, lots of awkward pieces |
| `chaos` | all 34 pieces equally likely |
| `progressive` **(default)** | classic at first, then easy at 10 lines, normal at 20, hard from 30 |

## 4. Designing a variant without code: the Variant Designer

This is the main way to make your own variant. **No programming is needed.**

### Open it

| system | how |
|---|---|
| macOS | double-click `design.command` |
| Windows | double-click `design.bat` |
| Linux | `./design.sh` |
| any | `python3 design.py` (or `python3 design.py variants/classic.json` to open one) |

### The window

- **Left: the form.**
  - **About:** name, author, a short description.
  - **Board and speed:** width, height, starting fall delay, how often the
    game speeds up and by how much, the fastest it may get, and the size of
    one square on screen.
  - **Pieces:** choose one of three ways:
    - **Ready-made mode:** pick classic, easy, normal, hard, chaos or
      progressive from a list.
    - **My own mix:** one slider per group (the 7 classic pieces, and each
      difficulty class). A slider is a *share*; the sliders don't need to add
      up to 100.
    - **Gets harder as lines are cleared:** up to 4 stages, each a mode or
      "my mix" (the sliders), and how many lines each stage lasts.
- **Right: the live preview.** It changes as you edit:
  - a bar chart of the chance of each difficulty class;
  - the average holes per piece, with a word for it ("like classic
    Tetris", "easy", "medium", "hard", "very hard");
  - every piece that can appear, drawn in its class colour with its own
    chance;
  - for a "gets harder" variant, a slider to see the chances after any
    number of lines;
  - at the bottom, **problems to fix** in red, or a green "Ready" when the
    variant is complete.
- **Top: the buttons.**
  - **Play:** opens a game of your variant straight away.
  - **Robot playtest:** a robot plays 5 quick games and reports how many
    lines it cleared, how often it reached the top, and which pieces it got.
    For comparison, the same robot clears about 73 lines on classic Tetris
    and about 2 with all 34 pieces.
  - **Release…:** packages your variant as a **zip file to share** (see
    below).
  - **Save:** saves your variant as a `.json` file you can open again later
    (File ▸ Open…).

### Releasing your variant

**Release…** asks for a folder (normally `releases/`) and creates
`<your-variant-name>.zip`. Whoever receives it:

1. unzips it;
2. double-clicks `play.command` (macOS) or `play.bat` (Windows), or runs
   `./play.sh` (Linux).

The zip includes the game engine, your variant, the launchers, and a
`README.md` that describes your variant automatically: its settings, the
chance of each class, and how to play. The receiver only needs Python with
numpy and tkinter (`python3 play.py --check` tells them what's missing).

### Sample variants

The `variants` folder has four to open and change:

| file | what it is |
|---|---|
| `classic.json` | plain Tetris |
| `gentle-start.json` | classic, then easy, then normal; speeds up every 10 lines |
| `wide-board.json` | a 14 × 22 board with extra long bars |
| `corner-climb.json` | classic, then a home-made mix, then hard, then chaos |

Also available from a terminal:

```bash
python3 play.py --variant variants/gentle-start.json    # play a saved variant
python3 play.py --release variants/gentle-start.json    # make its zip in releases/
```

## 5. Making a variant in Python (optional)

If you're comfortable editing a short text file, you can also write a variant
in Python. This is how programmers use ExTetris as a library. The easiest way
is to **copy an example and change it**. The `examples`
folder has three:

| file | what it shows |
|---|---|
| `examples/classic_tetris.py` | the simplest possible variant: one setting |
| `examples/gentle_start.py` | a progressive game that also speeds up sooner |
| `examples/wide_board_custom_mix.py` | a bigger board and a hand-made piece mix |

Steps:

1. Copy one of them, e.g. `examples/gentle_start.py` → `examples/my_game.py`.
2. Open the copy in any text editor and change the values inside `Game(...)`.
3. Run it: `python3 examples/my_game.py`.

The only part you need to change looks like this:

```python
def make_game():
    return Game(
        pieces="easy",          # which pieces appear (see section 6)
        width=10, height=20,    # board size
    )
```

Rules for editing:

- Keep the commas between settings.
- Put names in quotes: `"easy"`, `"TwoHole"`.
- Settings you leave out keep their normal value.
- Lines starting with `#` are notes for people; Python ignores them.

### All the settings

| setting | what it does | normal value |
|---|---|---|
| `width` | board width in squares (at least 4) | `10` |
| `height` | board height in squares (at least 4) | `20` |
| `pieces` | which pieces appear and how often (section 6) | `"progressive"` |
| `start_delay_ms` | milliseconds between automatic one-row falls at the start; smaller = faster | `1000` |
| `speedup_every` | lines to clear before pieces fall faster | `100` |
| `speedup_factor` | how much faster each time: `0.9` means 10 % less waiting | `0.9` |
| `min_delay_ms` | the game never gets faster than this | `50` |
| `rng` | a fixed random seed, so the same pieces come every time, e.g. `random.Random(42)` (needs `import random` at the top) | random |

Window settings go in the `GameWindow(...)` line at the bottom of the
example files: `title="My Game"` and `cell_size=24` (the size of one square in
pixels).

## 6. Choosing the pieces in Python

`pieces=` accepts three kinds of value.

### a) A mode name

```python
Game(pieces="hard")
```

### b) A mix of your own: `mix(...)`

Give each group a **share**. The shares don't have to add up to 100.

```python
from extetris import Game, mix

Game(pieces=mix(classic=70, TwoHole=20, I=10))
```

That means 70 % of pieces are classic, 20 % are two-hole pieces, and an extra
10 % are I bars (so I is more common than the other classics).

| you can write | meaning |
|---|---|
| `classic=...` | the 7 normal pieces, sharing this amount equally |
| `all=...` | all 34 pieces, sharing equally |
| `NoHole=...`, `TwoHole=...`, … | every piece in that class, sharing equally |
| `I=...`, `T=...`, `S=...` | one particular piece |

Names with a dash or Γ can't be written this way. Put them in `{ }` with quotes
instead:

```python
mix({"TwoHole-03": 5, "Γ": 2, "classic": 50})
```

To make some pieces **equally likely and nothing else**, use `only`:

```python
from extetris import Game, only

Game(pieces=only("I", "O", "T"))
```

### c) A game that gets harder: `progressive(...)`

```python
from extetris import Game, progressive

Game(pieces=progressive(["classic", "easy", "hard"], every_lines=5))
```

This uses the first list item at the start and moves to the next one every
`every_lines` lines cleared, staying on the last. The list items can be mode
names or your own `mix(...)`.

### Checking a mix before you play

This prints what share each class gets:

```bash
PYTHONPATH=src python3 -c "from extetris import mix; print(mix(classic=70, TwoHole=30).probabilities_by_class())"
```

## 7. For programmers: going further

These need a little Python, but each is only a line or two.

- **Any rule you like.** A mix is just a function that takes a piece's facts
  and the lines cleared, and returns a weight:

  ```python
  from extetris import PieceMix
  # only pieces whose bounding box is 3 squares long, more of them as lines go up
  PieceMix(lambda info, lines: (1 + lines) if info.box_size.startswith("3") else 0)
  ```

  A piece's facts (`info`) include `name`, `piece_class`, `box_size` (e.g.
  `"4x2"`), `touching` (`"edges"` or `"corners"`), `chiral` (has a mirror
  twin) and `spawn_holes`.
- **Your own piece function.** `pieces=` also accepts any function that takes
  a random generator and returns a piece, e.g.
  `lambda rng: NoHole("T", rng=rng)`.
- **Without a window.** `Game` works on its own:
  `g = Game(); g.move_left(); g.hard_drop(); print(g.render())`.
- **Everything else** is in the [API reference](api.md).

## 8. Troubleshooting

| problem | what to do |
|---|---|
| The designer shows problems in red | each line says what to change; Play, Robot playtest and Release work once it shows the green "Ready" |
| macOS says `design.command` can't be opened | right-click it → Open → Open (only needed the first time) |
| "numpy is missing" | `python3 -m pip install numpy` (Windows: `py -m pip install numpy`) |
| "tkinter is missing" | macOS / Windows: install Python from python.org. Linux: `sudo apt install python3-tk` |
| macOS says `play.command` can't be opened | right-click it → Open → Open (only needed the first time) |
| The window doesn't appear | it may be behind other windows; look for the Python icon in the Dock or taskbar |
| `unknown mode 'xyz'` | check the spelling; the modes are classic, easy, normal, hard, chaos, progressive |
| `unknown piece or group 'xyz'` | check the name with `python3 play.py --catalogue`; names are case-sensitive |
| `'S' is a OneHole piece, not a NoHole piece; use OneHole('S')` | the message says exactly what to write instead |
| `SyntaxError` after editing | usually a missing comma or quote; compare with the example you copied |
