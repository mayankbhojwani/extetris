# AI Interaction Raw Log

Assistant: Claude Code (model: Claude Opus 5.5), Claude desktop app, Code tab.
Each entry has the prompt **verbatim** and a summary of the assistant's
response. The interpretation and plan sections of the report are written
separately by the student.

---

## Entry 1 (2026-11-22 06:00 IST, Phase 1 analysis)

### Prompt (verbatim)

```text
Read PoPL2026AssignmentExTetris.pdf and the starter code in extetris/ (engine.py, board.py, shape.py, allextetrominoes.py). This is my course assignment for CS F301 PoPL. AI use is allowed, but I must report every interaction verbatim, so work in phases and STOP at each checkpoint for my decision. Do not run ahead.

Ground rules for the whole session:
- Keep extetris/ untouched as the reference. Build the new engine in src/extetris/.
- Append every prompt I give you and a summary of your response to docs/ai_log/raw_log.md, with a timestamp. Also give me a short "what changed / what I should verify" note at each checkpoint. I'll write the interpretation and plan sections of the report myself.
- Python 3, numpy and tkinter only, unless you ask first.

PHASE 1 (analysis only, no new code):
1. Write a script that normalises all 73 matrices under rotation (and separately under rotation plus reflection), removes duplicates, and reports how many distinct shapes there are. Group them by bounding box and by edge-connected vs corner-connected.
2. For each distinct shape and orientation, count the holes it leaves when it lands on a flat floor (empty cells under filled cells in each column of the piece).
3. List the bugs in the starter code (missing imports, the shared-matrix bug in rotate_CW, the pasueStatus typo, etc.).
4. Write it all up in docs/analysis.md. Then STOP and propose 2-3 alternative shape class hierarchies with trade-offs: classify by bounding box vs by hole profile vs a parameterised generator. Don't pick one.
```

### Response summary (finished 2026-11-22 06:06 IST)

**Actions taken**

- Read the PDF (16 pages) and the four starter files. The starter files sit at
  the project root, not in an `extetris/`
  subfolder. The assistant treated the root files as the untouched reference
  and pointed this out to the student.
- Ran headless reproduction snippets (no files written) to confirm the
  suspected bugs.
- Created `tools/shape_census.py` (Python 3 + numpy). It loads
  `allextetrominoes.py` by path without writing bytecode, then trims and
  deduplicates the matrices (exact, under rotation, under rotation +
  reflection). It also enumerates every 4-cell edge-or-corner-connected shape
  from scratch, groups shapes by bounding box × connectivity, and computes
  per-orientation hole profiles on a flat floor. With `--write` it produces
  `docs/generated/shape_census.md` and `.json`.
- Wrote `docs/analysis.md`.
- Wrote no engine code and changed nothing in the reference files.

**Key results**

- 73 matrices, no malformed ones. 71 distinct fixed orientations (#1 = #10 = #11).
- **34** distinct shapes under rotation and **22** under rotation + reflection.
  An independent enumeration finds exactly 34 / 22, so the starter set is
  exhaustive up to rotation (71 of 110 fixed orientations).
- By connectivity: 7 one-sided classes are edge-connected and 27
  corner-connected (5 and 17 as free classes). By bounding box, the one-sided
  classes split 4x1:1, 2x2:1, 3x2:7, 3x3:9, 4x2:9, 4x3:6, 4x4:1.
- Shapes are repeated unevenly in the index list (1 to 4 times each). A
  "uniform" `range(1,74)` gives each 3x3 shape 5.5 % and O/T/L/Z 1.4 % each.
  #23 is a rotated classic S.
- Minimum flat-floor holes per shape range from 0 to 6 (0:5, 1:10, 2:11, 3:3,
  4:4, 6:1 shapes). This does not follow bounding box. Mirror pairs have the
  same hole counts. The starter's spawn orientation is often the worst one.
- Bugs: B1 shared-matrix aliasing in rotate (a blocked rotation can flip or
  mirror the piece; verified). B2 global templates get mutated. B3 mutable
  default argument in `Shape`. B4 negative-index wrap lets pieces leave the
  left/top edge (verified). B5 the `pasueStatus` typo. B6 pressing Down while
  paused starts extra gravity timers (verified). B7 `game_over_status` is never
  set. B8 the speed-up modulo check can be skipped. B9 `eval`/`input` crashes
  and NameErrors. B10 row-width/wrap misrendering.
- Implicit dependencies: `numpy` arrives through the star import, and
  `tk.simpledialog` arrives through `filedialog`'s internal import. Both work
  on Python 3.13 but only by accident, so the assistant listed them as fragile
  dependencies, not crashes.
- Also listed 8 design limitations.

**Checkpoint proposal: three alternative shape class hierarchies (no choice
made)**

- A. **By bounding box.** `ExTetromino` base, one subclass per box (`Box4x1`
  ... `Box4x4`), with a variant/chirality parameter in each constructor.
  Pros: matches the brief's "4x2" wording, has only 7 classes, and the box
  drives spawn position and edge collisions. Cons: groups are very uneven
  (1 to 9), each subclass still needs a table of variants, connectivity cuts
  across the boxes, and the box says nothing about difficulty.
- B. **By hole profile / difficulty tier.** Subclasses by minimum flat-floor
  holes (0, 1, 2, 3, 4, 6), or by hole-profile family. Pros: speaks to the
  brief's "holes produced while landing" and lets probabilities be given per
  difficulty tier. Cons: holes depend on orientation, so membership has to be
  defined by the minimum or spawn orientation. The class doesn't determine the
  geometry, tiers are uneven, and the rule assumes a flat floor.
- C. **Parameterised generator.** A few generative subclasses, e.g.
  `Polyform(n, connectivity)` that enumerates shapes, or compositional ones
  (straight runs, dominoes joined at a corner, diagonals). Bounding box, holes
  and chirality become computed attributes that can be used as filters and
  weights. Pros: no hard-coded matrices, extends to n=5, and the
  classification is guaranteed consistent. Cons: shallower inheritance, so it
  looks data-driven unless paired with named subclasses. It also needs a
  registry or catalogue so game designers can refer to shapes by name.

The assistant stopped at the checkpoint and waited for the student's decision.

---

## Entry 2 (2026-11-22 06:08 IST, clarification)

### Prompt (verbatim)

```text
i don't understand anything happening here
```

### Response summary

No files changed except this log. The assistant re-explained Phase 1 in plain
language: what the assignment asks for, what the analysis found (73 entries are
really 34 different pieces, or 22 if mirror images count as the same; a "holes"
count for how awkward each piece is; bugs such as a blocked rotation secretly
mirroring a piece and pieces sliding off the left edge). It then described the
pending decision as three ways to sort the pieces into classes (by box size, by
difficulty, or by a recipe that generates them), using an analogy, and asked
which part was unclear.

---

## Entry 3 (2026-11-22 06:14 IST, clarification)

### Prompt (verbatim)

```text
Walk through the findings
```

### Response summary

No files changed except this log. The assistant walked through the Phase 1
findings step by step in plain language, with small text drawings:
(1) why 73 entries reduce to 34 pieces (same piece turned) and 22 (mirror images
merged), and which entries repeat; (2) edge-touching vs corner-touching pieces
and bounding-box sizes; (3) how the hole count is measured, with worked examples
(T piece, diagonal piece); (4) the uneven piece frequencies; (5) the most
important starter-code bugs, each explained with what a player would see.

---

## Entry 4 (2026-11-22 06:20 IST, clarification)

### Prompt (verbatim)

```text
Explain the 3 options
```

### Response summary

No files changed except this log. The assistant explained the three candidate
shape class hierarchies in plain language. For each option it described the
idea, a short illustrative sketch of what the classes and a game designer's
code might look like, what it does well, and what it does badly: (A) one class
per bounding-box size, (B) one class per difficulty tier (fewest holes), and
(C) a generator class that builds every piece from rules, with size and
difficulty as looked-up properties. It also restated what the professor's brief
asks for, so the options could be compared against it, and listed questions to
help the student decide. No option was recommended.

---

## Entry 5 (2026-11-22 15:34 IST, design question)

### Prompt (verbatim)

```text
can I use somewhat as a mixture of B and C
```

### Response summary

No files changed except this log. The assistant said yes and sketched a B+C
hybrid. A generator (C) builds every piece from a rule, so no grids are typed
by hand. Difficulty-tier subclasses (B) form the visible class hierarchy, and
each tier pulls its pieces from the generator. Box size and edge/corner
touching stay as labels each piece carries. Piece frequency is set per tier
through a small weighting function instead of repeated indices. It listed the
open choices the student must make:
1. Tier is defined by the fewest holes in any orientation (fixed per shape)
   rather than by spawn orientation.
2. Whether to merge the small tiers (3, 4 and 6 holes; there is no 5-hole
   tier) into one "hard" tier.
3. How pieces get names.
4. Whether to keep a second level split by edge/corner touching.
It gave the hybrid's trade-offs and did not start Phase 2.

---

## Entry 6 (2026-11-22 15:43 IST, design decisions)

### Prompt (verbatim)

```text
b)
keep separate for now will see later
just auto names
let's keep this on hold for now will add if needed later
```

### Response summary

No files changed except this log. The assistant recorded the student's
decisions for the B+C hybrid:
1. A piece's difficulty class comes from the holes it leaves in its **spawn
   orientation** (option b).
2. The hole levels stay as separate classes, with no merging for now.
3. The 27 non-classic pieces get automatic names.
4. No second level split by edge/corner touching for now (on hold).

The assistant pointed out a consequence of decision 1. Because the generator
stores no hand-typed grids, "spawn orientation" needs a rule. It showed, from
the Phase 1 census, how the classes would fill if the starter file's
orientations were used (0 holes: 2 pieces; 1: 4; 2: 10; 3: 8; 4: 7; 5: 2;
6: 1). This differs from the best-orientation grouping: L, T and Γ move from
the 0-hole class to the 2-hole class. It then asked the student to choose the
spawn rule and to define the scope of Phase 2. No code was written.

---

## Entry 7 (2026-11-22 15:45 IST, design decision)

### Prompt (verbatim)

```text
Flattest turn
```

### Response summary

No project files changed except this log. The assistant recorded the spawn
rule: a piece appears in its flattest turn (least height); if two turns are
equally flat, it takes the one with fewer holes. It ran a quick check that
used the Phase 1 census functions and wrote nothing.

The resulting classes are:

| holes | pieces |
|---|---|
| 0 | I, O, L, T, Γ |
| 1 | 10 |
| 2 | 11 |
| 3 | 3 |
| 4 | 4 |
| 6 | 1 |

This is exactly the same grouping as the "best turn" rule. For 13 shapes, two
flat turns still tie on holes but look different. That affects only how the
piece looks when it appears, not its class. The assistant asked the student to
choose a final tie-break (a fixed choice or random between the tied turns) and
to define the scope of Phase 2. No code was written.

---

## Entry 8 (2026-11-22 15:46 IST, design decision)

### Prompt (verbatim)

```text
Random between ties
```

### Response summary

No files changed except this log. The assistant recorded the decision: when a
piece's flat turns tie on holes, it spawns in one of the tied turns at random.
This does not change the piece's difficulty class. The design decisions so far
are:

- B+C hybrid: a generator builds the pieces, and difficulty classes form the
  hierarchy.
- A piece's class comes from the holes it leaves in its spawn turn.
- The spawn turn is the flattest one, with fewer holes breaking ties, then a
  random pick between turns that still tie.
- Hole levels stay as separate classes.
- Pieces are named automatically.
- No edge/corner split for now.

It then proposed a scope for Phase 2 and asked for approval:

- Build only the piece layer in `src/extetris/`:
  - an immutable Shape base that fixes starter bugs B1-B3,
  - the piece generator,
  - the difficulty classes with automatic names,
  - the spawn rule.
- Add tests that check the results against the Phase 1 census.
- Leave out the board, engine, GUI and piece frequencies.

No code was written.

---

## Entry 9 (2026-11-22 15:50 IST, Phase 2: piece layer)

### Prompt (verbatim)

```text
Yes, start Phase 2
```

### Response summary

The assistant built the agreed Phase 2 scope (piece layer only) in
`src/extetris/`. Only Python 3, numpy and the standard library are used.

**Files created**

| file | contents |
|---|---|
| `geometry.py` | pure functions on read-only matrices: trim, rotate, mirror, keys for rotation/mirror classes, touching (edges/corners), box size, hole profile, and `spawn_turns` (flattest turn, then fewest holes; remaining ties are all returned) |
| `generator.py` | `PieceGenerator(n_cells, touching)`: grows every shape one square at a time; returns one matrix per piece in a fixed, sorted order; `free_shapes()` also merges mirror images |
| `shape.py` | immutable `Shape` base class; `rotated_cw()` and `rotated_ccw()` return new objects; the matrix is a read-only copy (fixes starter bugs B1-B3) |
| `pieces.py` | `ExTetromino(Shape)` plus difficulty classes `NoHole`, `OneHole`, `TwoHole`, `ThreeHole`, `FourHole`, `SixHole` (by spawn-turn holes; no 5-hole piece exists); see below |
| `__init__.py` | package exports |
| `__main__.py` | prints the catalogue: `PYTHONPATH=src python3 -m extetris` |
| `tests/test_pieces.py` | 28 unittest tests |

Details of `pieces.py`:

- The 7 classic pieces are named by rules on their properties, with no stored
  grids. "Gamma" and "J" are accepted as aliases for Γ.
- The other pieces get automatic names `<Class>-NN`.
- A spawn turn is picked at random among tied turns, using an optional
  `random.Random` so games can be replayed.
- Lookups: by name, by number, or `ExTetromino.named()`.
- A wrong class or an unknown name raises a clear error.

**Result**

All 28 tests pass (0.15 s). They check:

- counts 34 / 22 pieces, 7 / 5 for edges only, 18 / 12 for pentominoes;
- the generated set equals the starter file's set;
- class sizes 5 / 10 / 11 / 3 / 4 / 1;
- spawned pieces always have their class's hole count;
- 13 pieces have tied spawn turns, and both turns occur;
- immutability (no mutation, no mirroring, the catalogue is unaffected);
- classic names match the starter comments;
- the same seed gives the same pieces.

Reference starter files are unchanged.

**Points flagged for the student**

- The difficulty subclasses share one constructor and differ only by the
  class attribute `SPAWN_HOLES`. The brief says constructors "must be
  overridden in each subclass", so this is a design point to decide on.
- Rotation pivot and wall kicks are left to the engine phase.
- Piece frequencies are not done yet.

---

## Entry 10 (2026-11-22 15:51 IST, verification)

### Prompt

The student ran `PYTHONPATH=src python3 -B -m extetris` in their own terminal
and the catalogue output was shared with the assistant. The output itself is
not repeated here. Before that, the student ran the test suite (28 tests, all
OK).

### Response summary

The assistant fixed one cosmetic bug in `src/extetris/__main__.py`: the
heading said "1 pieces" instead of "1 piece". It then explained how to read the
catalogue: two hand-checked hole counts, why 3x3 pieces show 3 rows, and that
mirror twins land in the same class. The constructor design question is still
open.

---

## Entry 11 (2026-11-22 15:51 IST, clarification)

### Prompt (verbatim)

```text
would does the assignment ask for
```

### Response summary

No files changed except this log. The assistant explained what the brief says
about subclass constructors. In "The Division of Labour" (section 2), the brief
expects the simple constructor to grow complicated and be overridden in each
subclass. Section 2 also asks for subclasses "instantiated by different input
parameters" (e.g. "4x2" shapes) and calls this a design choice to make after
experimenting. The abstract stresses creative licence.

The assistant noted the following:

- The current design moves the complicated work into the generator, so each
  difficulty class has nothing of its own to do in a constructor.
- That follows the spirit of the brief (no hand-typed data, one place for the
  logic) but not its literal wording.
- Each class could get its own constructor that does real work, at a small
  cost.
- Either way, the report should explain the choice.

The decision was left to the student.

---

## Entry 12 (2026-11-22 15:53 IST, clarification)

### Prompt (verbatim)

```text
what are the pros of each having its own constructor
```

### Response summary

No files changed except this log. The assistant listed the advantages of
giving each difficulty class its own constructor:

1. It matches the brief's wording, which is safer for grading.
2. It shows the PoPL ideas of method overriding and super() chaining
   explicitly.
3. Each class documents its own arguments, so help(TwoHole) is self-contained.
4. Errors can be specific to each class.
5. It leaves room for per-class behaviour later, such as score bonuses,
   colours or kinder spawn rules for hard pieces.
6. The UML diagram shows a constructor on every class.
7. It gives game programmers a pattern to copy for their own piece classes.

It briefly restated the main drawback: more code that is mostly similar. The
decision was left to the student.

---

## Entry 13 (2026-11-22 15:54 IST, design decision + code change)

### Prompt (verbatim)

```text
Give each its own
```

### Response summary

The assistant changed `src/extetris/pieces.py` so that every difficulty class
(`NoHole` … `SixHole`) overrides `__init__(self, variant=None, rng=None)`:

- Each constructor has its own docstring listing exactly the names and numbers
  its class accepts.
- Each one calls `super().__init__(variant, rng)`, so the shared work of
  choosing a piece and its spawn turn stays in `ExTetromino`.
- `SixHole` has a class-specific rule: a number other than 1 raises "there is
  only one six-hole piece".
- The shared error message now suggests the right class, e.g. "'S' is a
  OneHole piece, not a NoHole piece; use OneHole('S')".
- A comment above the classes explains why each class overrides the
  constructor.

It added 4 tests (class `TestConstructors`):

- each class defines its own documented `__init__`;
- the overrides still reach the shared work;
- the wrong-class message suggests the right class;
- the SixHole rule.

All 32 tests pass. The catalogue output is unchanged (5 / 10 / 11 / 3 / 4 / 1).

---

## Entry 14 (2026-11-22 15:58 IST, Phase 3: game board)

### Prompt (verbatim)

```text
okay phase 3 let's build the game board
```

A second message arrived while the assistant was working (verbatim):

```text
also start pushing this on github coz why not don't show claude
```

### Response summary

**Board (Phase 3)**

The assistant created `src/extetris/board.py` with an immutable
`Board(width=10, height=20)` class. Width and height must be at least 4 so
every piece fits. It has these methods:

| method | what it does |
|---|---|
| `fits(piece, row, col)` | checks all four edges explicitly, so negative positions are off the board (fixes starter bug B4) |
| `place()` | returns a new board with the piece fixed in place |
| `drop_row()` | the row where a piece would land |
| `full_rows()` | lists the full rows |
| `clear_full_rows()` | returns (new board, number of rows cleared) |
| `holes()` | counts holes using the same rule as for pieces |
| `render()` | draws the board with one character per square (fixes B10); an optional falling piece is shown with '▒' |
| `from_text()` | builds a board from '#'/'.' lines |

`Board` is exported from the package.

It added `tests/test_board.py` with 26 tests, including:

- regressions for B4 and B10;
- the Phase 1 line-clear case;
- a cross-check that every turn of every piece, dropped on an empty board,
  leaves exactly `piece.holes` holes.

On the first run, one test failed because the assistant's expected value in
that test was wrong (2 instead of 3; the code was right). The assistant fixed
the test. All 58 tests now pass.

Left for the engine phase: rotation pivot and wall kicks, gravity, keys,
scoring and game over.

**GitHub**

The assistant took "don't show claude" to mean no Claude co-author or
attribution lines in commits. It kept this AI log in the repository because
the assignment requires reporting AI use. It found that the GitHub CLI is
logged in but git has no user.name set. It asked the student about repository
visibility, whether to include the professor's PDF and starter code, the
repository name and the commit author name before creating anything.

---

## Entry 15 (2026-11-22 16:01 IST, GitHub setup)

### Prompt

The student answered the assistant's setup questions:

- Visibility: **Public**.
- Professor's files: "Starter code, no PDF".
- Repository name: "extetris".
- Commit author: "mayankbhojwani".
- Commit email: "Use noreply address" (after the assistant warned that their
  Gmail address would be public).

### Response summary

The assistant:

- created a `.gitignore` that excludes caches, .DS_Store and the assignment
  PDF;
- ran `git init` with branch main;
- set the author name and the GitHub noreply email for this project only;
- removed the local folder path (which contains the computer's username) from
  Entry 1 of this log before publishing;
- made one commit with no Claude attribution lines;
- created the public repository mayankbhojwani/extetris and pushed.

---

## Entry 16 (2026-11-22 16:07 IST, Phase 4: game engine and window)

### Prompt (verbatim)

```text
let's wrap up the game engine and window first
```

(Earlier messages in this stretch were the student running the verification
commands in their own terminal: the tests, the help text, the catalogue and
board drawings. The assistant confirmed the outputs; no code changed.)

### Response summary

The assistant built Phase 4 as two separate layers.

**`src/extetris/game.py`: `Game` (the rules, no tkinter)**

- Configurable board size, piece source (a function rng -> piece; the default
  `any_piece` makes all 34 pieces equally likely, and the piece-frequency
  phase will plug in here), seeded rng, start delay, and speed-up settings
  (default: every 100 lines x0.9, as in the starter).
- Pieces spawn at the top centre; game over when the new piece can't fit.
- Moves:
  - left/right;
  - turning clockwise and anticlockwise, kept centred, with wall kicks
    (shifts of 0, ±1, ±2 columns, or 1 row up);
  - soft drop;
  - hard drop, which locks immediately;
  - a gravity tick that locks the piece and clears rows.
- Speed-ups count every multiple of 100 lines crossed.
- Pause and new game; `render()` gives a text picture.
- Fixes B5, B7, B8, L1 and L3.

**`src/extetris/window.py`: `GameWindow` (tkinter Canvas)**

- Draws coloured squares, with the piece colour showing its difficulty class.
- Keys: arrows, Z for anticlockwise, Space, P.
- Menus: New Game, Pause/Resume, Speed Up/Down, Save Board as Text, Quit,
  Keys, About.
- Exactly one gravity timer, always cancelled before rescheduling.
- Dialogs restore the previous pause state.
- The status line shows lines, pieces, fall delay, and the current and next
  piece.
- Fixes B6, B5, B10, D2, L2 and L5.

**Entry points**

- `python3 play.py` plays the game.
- `python3 play.py --catalogue` lists the pieces (the old catalogue printer
  moved to `catalogue.py`).
- The starter's `engine.py` is still untouched.

**Tests:** `tests/test_game.py`, 20 tests:

- moves and walls (B4 at game level) and a right-wall kick;
- hard drop locking (L3), line counting, and the 99 -> 101 speed-up (B8);
- pause blocking every move, game over, and a new game after game over (B7);
- 3000-step random-play fuzz checks (the piece is always on the board, no full
  rows are left) and seeded replay;
- hidden-window checks, including exactly one timer after keys pressed while
  paused (B6).

The first run had 1 failure: 2 timers instead of 1. The cause was that
`_gravity` cleared its timer record before rescheduling, so calling it
directly (as the test did) left the old timer running. The assistant fixed
this in `window.py`. All 78 tests now pass. The assistant also opened the real
window for 1.5 s and closed it automatically. The game has not been played by
hand yet; that is for the student to check.

---

## Entry 17 (2026-11-22 16:10 IST, manual play check)

### Prompt (verbatim)

```text
they cant go through wals
```

(Before this, the student ran `python3 play.py` in their terminal; it exited
with no errors.)

### Response summary

No files changed except this log. The assistant noted the result: by hand,
pieces stop at both walls, confirming the fix for starter bug B4. It listed
the remaining manual checks: turning next to a wall, Space locking, pause and
About, clearing a row, and New Game after Game Over.

---

## Entry 18 (2026-11-22 16:12 IST, design question)

### Prompt (verbatim)

```text
it seems fine but do we have to use all these type of pieces kinda makes the game boring?
```

(Before this, the student ran `python3 play.py` twice more; both runs exited
with no errors.)

### Response summary

No files changed except this log. The assistant explained that using all 34
pieces is not required. The current default (all 34 equally likely, so about 4
in 5 pieces are corner-touching ones) was only a placeholder. The starter's own
default was the 7 classic pieces only. Choosing which pieces appear and how
often is exactly the brief's second requirement, replacing the "repeat the
index" trick, and the planned Phase 5.

It proposed three ways to control the piece mix, which can be combined:

- (A) a mix a designer sets by difficulty class or by individual piece;
- (B) ready-made modes: Classic, Easy, Normal, Hard, Chaos;
- (C) a progressive mix that starts with the classics and adds harder classes
  as more lines are cleared.

It recommended A as the base, with B and C built on it, and asked the student
to decide.

---

## Entry 19 (2026-11-22 16:15 IST, Phase 5: piece mixes)

### Prompt (verbatim)

```text
Yes, A + B + C
```

### Response summary

The assistant built Phase 5.

**`src/extetris/mixes.py` (functional-OO)**

A `PieceMix` wraps one function, weight(piece info, lines cleared) -> number.
Everything else creates new weight functions:

- (A) `mix(...)` takes weights for groups:
  - groups can be piece names, class names, "classic" or "all";
  - a group's weight is shared by its pieces;
  - overlapping groups add up.

  `only(...)` makes the chosen pieces equally likely.
- (B) `MODES`:
  - classic: the 7 classic pieces;
  - easy: classic 85, OneHole 15;
  - normal: classic 55, OneHole 20, TwoHole 15, ThreeHole 5, FourHole 4,
    SixHole 1;
  - hard: classic 25, OneHole 25, TwoHole 25, ThreeHole 12, FourHole 10,
    SixHole 3;
  - chaos: all 34 equally likely.
- (C) `progressive(stages, every_lines=10)` defaults to classic, then easy at
  10 lines, normal at 20 and hard from 30 on.

Helpers: `probabilities()`, `probabilities_by_class()`, `expected_holes()`
(a difficulty score) and `draw()`. Bad keys, negative weights or all-zero
weights raise clear errors.

**Integration**

- `Game(pieces=...)` replaces `piece_source`. It accepts a mode name, a
  PieceMix or any function rng -> piece. The **default is now
  "progressive"**, where the default used to be all 34 pieces equally.
  Progressive mixes see the current line count.
- `Game.set_pieces()` switches the mix mid-game.
- The window has a new "Pieces" menu (radio buttons for the 6 modes), and the
  status line shows the mode.
- `python3 play.py --mode easy` starts in a chosen mode; an unknown mode
  gives a clear error message.

**Tests:** `tests/test_mixes.py`, 21 tests:

- class sharing, the repeat-index replacement (I:3, O:1 gives 75 % / 25 %),
  names, aliases and groups, overlap, bad input, and a custom weight function;
- every mode adds up to 1, and the modes get harder in order (by average
  holes);
- a 5000-draw frequency check;
- progressive stages;
- the Game integration.

`tests/test_game.py` was updated for the renamed parameter. All 99 tests pass.
A hidden-window check in easy mode worked.

**Average spawn holes per mode**

| mode | average holes |
|---|---|
| classic | 0.29 |
| easy | 0.39 |
| normal | 1.03 |
| hard | 1.76 |
| chaos | 1.85 |

The assistant pointed out that "hard" is close to "chaos". The mode weights
are design choices the student may want to tune.

---

## Entry 20 (2026-11-22 16:16 IST, design decision)

### Prompt (verbatim)

```text
Keep as is
```

### Response summary

No code changed. The assistant recorded the decision to keep the Phase 5 mode
weights as they are, including "hard" being close to "chaos" (1.76 vs 1.85
average spawn holes). It listed the parts of the brief still open:

- the documentation, the brief's "most important part": design documents with
  UML diagrams, API documentation, a Game Programmer's Manual, and the AI usage
  report;
- run/build scripts for non-programmers.

---

## Entry 21 (2026-11-22 17:12 IST, Phase 6: documentation)

### Prompt (verbatim)

```text
Documentation
```

A second message arrived while the assistant was working (verbatim):

```text
also build the scripts after this i'll be back
```

### Response summary (documentation part)

**API reference**

- `tools/make_api_docs.py` generates `docs/api.md` from the docstrings using
  `inspect`. It stops with an error if any exported name is undocumented.
- The first generated version showed 21 members with no docstring. The
  assistant added short docstrings to them in `game.py`, `window.py`,
  `pieces.py`, `shape.py` and `board.py` (no behaviour change).
- Signatures in the reference are shown without `self`.

**`docs/design.md`**

Goals, a layer diagram, a UML class diagram and a sequence diagram (what
happens on Space). All diagrams are Mermaid, which GitHub draws. It also
records:

- the design decisions taken at each checkpoint;
- a table mapping each starter bug to the place it was fixed;
- the testing summary;
- known limitations.

The assistant checked that all 3 Mermaid diagrams render without errors. It
did this by loading them with mermaid@10.9.1 in the built-in browser, from a
temporary local web server that it stopped afterwards. Before that check it
had simplified some diagram syntax (one-line class bodies, bracketed return
types).

**`docs/manual.md`: Game Programmer's Manual (plain language)**

- requirements, how to play, keys, menus and piece colours;
- the pieces and the modes;
- copying and editing an example, and a table of every setting;
- `mix` / `only` / `progressive` recipes;
- a "for programmers" section;
- troubleshooting.

**Other files**

- `examples/`: `classic_tetris.py`, `gentle_start.py`,
  `wide_board_custom_mix.py`. Each has a `make_game()` function.
- `README.md`: play instructions, a documentation index, the folder layout,
  and the licence (GPL-3.0, inherited from the starter).
- `tests/test_examples.py`: 4 tests that run every example and every manual
  code snippet.

All 103 tests pass. Each example window opened and closed automatically.
The README and manual already refer to `play.sh`, `play.command`,
`play.bat` and the Makefile, which are built in the next step.

---

## Entry 22 (2026-11-22 17:16 IST, Phase 7: run scripts)

### Prompt (verbatim)

The request came mid-turn during Phase 6 and is quoted in Entry 21:

```text
also build the scripts after this i'll be back
```

### Response summary

The student was away, so the assistant built and pushed this phase without a
checkpoint, as the message asked.

**Files**

| file | what it does |
|---|---|
| `play.py` | now checks Python 3.9+, numpy and tkinter first and prints plain install instructions if any is missing; new `--check` option prints the versions |
| `play.sh` (macOS/Linux) | finds python3 or python (3.9+) and runs `play.py` with any options passed |
| `play.command` (macOS) | double-click launcher; keeps the Terminal window open with a message if something goes wrong |
| `play.bat` (Windows) | double-click launcher; uses `py -3`, falling back to `python`, and pauses with an install hint on error; CRLF line endings |
| `Makefile` | play (`MODE=...`), check, catalogue, test, docs, census, clean; `clean` only touches the new folders, never the starter's |
| `.gitattributes` | keeps CRLF for .bat and LF for .sh/.command |

**Tests on this Mac**

- `./play.sh --check` reports Python 3.13.13, numpy 2.5.1 and Tk 8.6.
- An unknown `--mode` gives a clear message and exit code 1.
- `--catalogue` works.
- `make test`: 103 tests OK.
- A simulated missing numpy prints the install instructions.
- `./play.sh`, `./play.command` and `make play MODE=easy` each opened the
  game window, which was still running after 2.5 s, and were then stopped.

The first launch test hung: killing the shell left the game process holding
the output pipe. The assistant stopped it and redid the test with output to a
file and process-group kill. macOS has no `timeout` command, so one attempt
had to be repeated without it.

**Not tested:** `play.bat`, since no Windows machine was available, and a
real double-click in Finder (the launch was tested from the command line).
