# Phase 1 Analysis: Starter Shapes and Starter Code

Scope: analysis only. No engine code has been written yet. The reference starter
code (`engine.py`, `board.py`, `shape.py`, `allextetrominoes.py` at the project
root) was read but not modified.

Reproduce the numbers with:

```bash
python3 tools/shape_census.py --write
```

That regenerates [generated/shape_census.md](generated/shape_census.md), which has
every shape drawn in every orientation, and
[generated/shape_census.json](generated/shape_census.json).

Terms used below:

| term | meaning |
|---|---|
| fixed shape | a matrix in one specific orientation |
| one-sided class | shapes equal up to **rotation** (mirror images count as different) |
| free class | shapes equal up to **rotation and reflection** |
| edge-connected | the 4 cells are joined through shared edges (the classic tetrominoes) |
| corner-connected | joined only when diagonal (corner) contact is allowed |
| bounding box | unordered `long x short` size of the tight box, e.g. `4x2` |

---

## 1. How many distinct shapes are there?

| measure | count |
|---|---|
| matrices in `allextetrominoes.py` | 73 |
| malformed (not 4 cells, loose bounding box, or disconnected) | 0 |
| distinct fixed orientations | 71 |
| exact duplicates | #1 = #10 = #11 (the I piece, "repeated for convenience") |
| **distinct under rotation (one-sided)** | **34** |
| **distinct under rotation + reflection (free)** | **22** |

### Is the starter set exhaustive?

The script also builds every 4-cell shape connected through edges or corners
from scratch. That gives 110 fixed shapes, 34 one-sided classes and 22 free
classes. The starter set contains all 34 one-sided classes, so it **is
exhaustive up to rotation**. It holds only 71 of the 110 fixed orientations, but
that doesn't matter because the engine rotates pieces at runtime.

The 22 free classes split as 10 achiral shapes plus 12 chiral pairs
(10 + 2×12 = 34 one-sided classes).

### Redundancy in the index list

The 73 indices are not one per shape. One-sided classes appear 1 to 4 times:

| appearances in the 73 | one-sided classes | probability each under `range(1,74)` |
|---|---|---|
| 1 | S02 (O), S03 (L), S04 (T), S05 (Γ), S07 (Z), S11, S13, S24, S26, S29, S30, S32 | 1.4 % |
| 2 | S06 (S, also #23), S08, S09, S10, S12, S14, S15, S25, S27, S28, S31, S33, S34 | 2.7 % |
| 3 | S01 (I: #1, #10, #11) | 4.1 % |
| 4 | S16–S23 (all eight 3x3 one-sided classes) | 5.5 % |

So a "uniform" draw over `range(1,74)` is **not** uniform over shapes. Each 3x3
corner shape is four times as likely as O, T, L or Z. Index #23 is a rotated
classic S piece, so the comment that the extended pieces start after #7 is not
quite true. This matters for the distribution requirement in §3.2 of the brief.

---

## 2. Grouping

### One-sided classes (34) by bounding box × connectivity

| bounding box | edge-connected | corner-connected | total |
|---|---|---|---|
| 4x1 | 1 (I) | 0 | 1 |
| 2x2 | 1 (O) | 0 | 1 |
| 3x2 | 5 (L, T, Γ, S, Z) | 2 (S08, S15) | 7 |
| 3x3 | 0 | 9 | 9 |
| 4x2 | 0 | 9 | 9 |
| 4x3 | 0 | 6 | 6 |
| 4x4 | 0 | 1 (diagonal) | 1 |
| **all** | **7** | **27** | **34** |

### Free classes (22) by bounding box × connectivity

| bounding box | edge-connected | corner-connected | total |
|---|---|---|---|
| 4x1 | 1 | 0 | 1 |
| 2x2 | 1 | 0 | 1 |
| 3x2 | 3 | 1 | 4 |
| 3x3 | 0 | 7 | 7 |
| 4x2 | 0 | 5 | 5 |
| 4x3 | 0 | 3 | 3 |
| 4x4 | 0 | 1 | 1 |
| **all** | **5** | **17** | **22** |

Observations:

- Every edge-connected shape fits in 3x2 or smaller (plus the straight I).
  Every shape with a 3x3 or larger box needs a corner link.
- Bounding box alone does not split the shapes into similar-sized groups:
  3x3 and 4x2 each hold 9 one-sided classes, while 4x1, 2x2 and 4x4 hold 1 each.
- `3x2` is the only box that contains both edge- and corner-connected shapes.

---

## 3. Holes on a flat floor

**Rule (as specified):** the piece rests with the bottom of its bounding box on
a flat floor. In each column of the piece, count the empty cells below that
column's topmost filled cell. The **hole profile** is the per-column list of
those counts, read left to right. The hole count is its sum.

Caveat: this rule counts every cell a straight drop cannot reach. Some of those
cells could still be filled by sliding a later piece in sideways (a "tuck"), so
it is an upper bound on permanent holes.

Summary per one-sided class. The full per-orientation tables, with drawings and
profiles, are in [generated/shape_census.md](generated/shape_census.md).

| id | starter # | box | conn. | rotations | holes per rotation (CW from the starter orientation) | min | max |
|---|---|---|---|---|---|---|---|
| S01 I | 1, 10, 11 | 4x1 | edge | 2 | 0 / 0 | 0 | 0 |
| S02 O | 2 | 2x2 | edge | 1 | 0 | 0 | 0 |
| S03 L | 3 | 3x2 | edge | 4 | 2 / 2 / 0 / 0 | 0 | 2 |
| S04 T | 4 | 3x2 | edge | 4 | 2 / 1 / 0 / 1 | 0 | 2 |
| S05 Γ | 5 | 3x2 | edge | 4 | 2 / 0 / 0 / 2 | 0 | 2 |
| S06 S | 6, 23 | 3x2 | edge | 2 | 1 / 1 | 1 | 1 |
| S07 Z | 7 | 3x2 | edge | 2 | 1 / 1 | 1 | 1 |
| S08 | 8, 9 | 3x2 | corner | 4 | 1 / 1 / 1 / 2 | 1 | 2 |
| S09 | 12, 18 | 4x2 | corner | 4 | 3 / 1 / 1 / 3 | 1 | 3 |
| S10 | 13, 20 | 4x2 | corner | 4 | 3 / 2 / 1 / 3 | 1 | 3 |
| S11 | 14 | 4x2 | corner | 2 | 2 / 2 | 2 | 2 |
| S12 | 15, 21 | 4x2 | corner | 4 | 3 / 3 / 1 / 2 | 1 | 3 |
| S13 | 16 | 4x2 | corner | 2 | 2 / 3 | 2 | 3 |
| S14 | 17, 19 | 4x2 | corner | 4 | 2 / 3 / 2 / 3 | 2 | 3 |
| S15 | 22, 24 | 3x2 | corner | 4 | 2 / 1 / 1 / 1 | 1 | 2 |
| S16 | 25, 38, 50, 54 | 3x3 | corner | 4 | 3 / 2 / 2 / 3 | 2 | 3 |
| S17 | 26, 43, 46, 53 | 3x3 | corner | 4 | 4 / 2 / 2 / 3 | 2 | 4 |
| S18 | 27, 33, 39, 57 | 3x3 | corner | 4 | 4 / 1 / 1 / 4 | 1 | 4 |
| S19 | 28, 30, 37, 56 | 3x3 | corner | 4 | 4 / 4 / 2 / 2 | 2 | 4 |
| S20 | 29, 34, 48, 52 | 3x3 | corner | 4 | 4 / 3 / 1 / 3 | 1 | 4 |
| S21 | 31, 36, 41, 55 | 3x3 | corner | 4 | 2 / 3 / 3 / 2 | 2 | 3 |
| S22 | 32, 40, 45, 49 | 3x3 | corner | 4 | 2 / 4 / 3 / 2 | 2 | 4 |
| S23 | 35, 42, 47, 51 | 3x3 | corner | 4 | 3 / 3 / 2 / 2 | 2 | 3 |
| S24 (X) | 44 | 3x3 | corner | 1 | 3 | 3 | 3 |
| S25 | 58, 61 | 4x3 | corner | 4 | 5 / 3 / 3 / 5 | 3 | 5 |
| S26 | 59 | 4x3 | corner | 2 | 4 / 4 | 4 | 4 |
| S27 | 60, 62 | 4x3 | corner | 4 | 4 / 5 / 4 / 4 | 4 | 5 |
| S28 | 63, 66 | 4x2 | corner | 4 | 1 / 3 / 3 / 1 | 1 | 3 |
| S29 | 64 | 4x2 | corner | 2 | 2 / 2 | 2 | 2 |
| S30 | 65 | 4x2 | corner | 2 | 3 / 2 | 2 | 3 |
| S31 | 67, 70 | 4x3 | corner | 4 | 3 / 5 / 5 / 3 | 3 | 5 |
| S32 | 68 | 4x3 | corner | 2 | 4 / 4 | 4 | 4 |
| S33 | 69, 71 | 4x3 | corner | 4 | 5 / 4 / 4 / 4 | 4 | 5 |
| S34 diag | 72, 73 | 4x4 | corner | 2 | 6 / 6 | 6 | 6 |

### Distribution of the best-orientation (minimum) hole count

| min holes | one-sided classes | which |
|---|---|---|
| 0 | 5 | I, O, L, T, Γ |
| 1 | 10 | S, Z, S08, S09, S10, S12, S15, S18, S20, S28 |
| 2 | 11 | S11, S13, S14, S16, S17, S19, S21, S22, S23, S29, S30 |
| 3 | 3 | S24, S25, S31 |
| 4 | 4 | S26, S27, S32, S33 |
| 6 | 1 | S34 |

Observations:

- Minimum hole count is a natural difficulty scale from 0 to 6, and it does
  **not** follow bounding box. For example, 3x3 shapes range from 1 (S18, S20)
  to 3 (S24), and 4x2 shapes range from 1 to 2.
- Mirror pairs always share the same multiset of per-rotation hole counts
  (L/Γ, S/Z, S16/S21, S17/S22, ...). So a hole-based classification works at
  the free-class level, with chirality as a parameter.
- The starter's spawn orientation is often the *worst* one. For example, L, T
  and Γ spawn in a 2-hole orientation. Spawn orientation could be a design knob.

---

## 4. Bugs and defects in the starter code

Line numbers refer to the reference files at the project root. Items marked
**[verified]** were reproduced headlessly with Python 3.13.13 and numpy 2.5.1,
without opening a Tk window.

### Correctness bugs

| # | where | defect | effect |
|---|---|---|---|
| B1 | `engine.py:88`, `:98` (+ `shape.py:29-37`) | **Shared-matrix aliasing in `rotate_CW` / `rotate_AntiCW`.** `Shape(self.piece.matrix)` wraps the *same* array, and `flipud` swaps rows **in place** before the collision check. | **[verified]** When a rotation is blocked, the current piece is still changed. A CW attempt leaves an L upside-down (`[[1,0,0],[1,1,1]]`). An anticlockwise attempt turns the L into its mirror image Γ (`[[1,1,1],[0,0,1]]`). A blocked rotation can reflect a piece. |
| B2 | `engine.py:208` + `allextetrominoes.py` globals | `new_piece` wraps the module-level `ExtetrominoK` array without copying, so B1 also mutates the **global template**. | **[verified]** One rotation attempt changes `Extetromino3` permanently. Later spawns of that shape come out in a drifted orientation, sometimes mirrored. |
| B3 | `shape.py:19` | Mutable default argument: `mat=numpy.array(...)` is created once and shared by every `Shape()` built with the default. | **[verified]** `Shape().matrix is Shape().matrix` is `True`. Rotating one default Shape changes all of them. |
| B4 | `board.py:45-54` | `collision` relies on `IndexError` for bounds. Negative indices **wrap** in numpy instead of raising. | **[verified]** A piece can move off the **left** edge (cursor `(0,-1)`) or above the top. `render` then draws the overhanging cells in the right-most column. `insertShape` would write them there too. |
| B5 | `engine.py:184` | Typo `self.pasueStatus = False`. It should be `pauseStatus`. | After *About*, the game stays paused until the user picks *Pause* from the menu. |
| B6 | `engine.py:119-125` | `move_down_force` calls `move_down_step(True)`. While paused, that branch calls `after(...)` regardless of `accelerated`. | **[verified]** Each Down press while paused starts an **extra gravity timer chain**, so the game speeds up for good after unpausing. |
| B7 | `engine.py:65`, `:213` | `game_over_status` is never set to `True`. | The check in `new_game` can never fire. Game over is handled only by `window.quit()`. |
| B8 | `engine.py:138` | Speed-up fires only when `deleted_lines % 100 == 0` right after a clear. | A multi-line clear that skips past a multiple of 100 (e.g. 99 → 101) never triggers the speed-up. |
| B9 | `engine.py:253`, `allextetrominoes.py:104,116` | `eval` builds variable names from input. `input()` is wrapped in `eval`, and the piece count maps to `range(1, n+8)`. | An answer above 66 makes the next spawn crash with `NameError`. Non-numeric input crashes at start-up. Because #10 and #11 are I, asking for 4 extra pieces triples the weight of I. |
| B10 | `board.py:24-33` + `engine.py:36-44` | Filled cells render as `⬛|` (2 characters) and empty cells as `  |` (3 characters). The `Text` widget is `2*width` characters wide with `wrap=tk.CHAR`. | Rows are 20 to 30 characters long in a 20-character widget, so they wrap and columns misalign. The starter comment on line 38 acknowledges this. |

### Fragile or implicit dependencies (work by accident)

| # | where | issue |
|---|---|---|
| D1 | `engine.py:137,163,166,215` | `numpy` is used but never imported. It only arrives through `from allextetrominoes import *`, because that module has no `__all__`, so `import *` also re-exports its `numpy`. **[verified]** This breaks as soon as the shapes module changes. |
| D2 | `engine.py:149,183` | `tk.simpledialog` is used but never imported. On this Python 3.13.13 it works only because `tkinter.filedialog` imports `tkinter.simpledialog` internally. **[verified]** That is an implementation detail of the standard library, not a guarantee. |
| D3 | `shape.py:20` | Checks the type by comparing `str(type(mat))` with a string. Subclasses of `ndarray` are rejected, and the error is a bare `Exception`. `isinstance` is the right tool. |

### Design limitations (not bugs, but they shape Phase 2)

| # | where | observation |
|---|---|---|
| L1 | `engine.py:86-104` | Rotation pivots on the bounding box's top-left corner (the cursor doesn't move) and has no wall-kick. Non-square pieces drift on rotation and often can't rotate next to a wall. |
| L2 | `engine.py:96` | `rotate_AntiCW` exists but no key is bound to it. `Shape.fliplr` is never used. |
| L3 | `engine.py:114-117` | Hard drop (Space) moves the piece down but doesn't lock it. Locking waits for the next gravity tick, so the player can still slide the piece. |
| L4 | `engine.py:25-71` | The engine is a single class that mixes Tk widgets, timers, rules, scoring and piece sampling. The constructor calls `mainloop()`, so you can't construct or test it without a GUI. |
| L5 | `engine.py:75-81` | `render` deep-copies the whole `Board` every 100 ms. The local `piece` variable is unused. |
| L6 | `engine.py:22-23` | Unused imports `time`, `sleep`, `copy`. |
| L7 | `engine.py:199-203` | *Save state* writes only the text rendering, and nothing can load it back. *Exit* and *Quit* do the same thing. |
| L8 | `allextetrominoes.py:105-116` | The shape distribution is expressed as a list of repeated **indices**. Because the index list is itself redundant (§1), the weights a designer gives aren't the probabilities players see. |

### Checked and found correct

- Line clearing (`engine.py:128-137`) handles several non-adjacent full rows
  correctly **[verified]** on a 4×6 board with full rows 3 and 5.
- `Shape.rotateCW` (`flipud` then `transpose`) and `rotateAntiCW`
  (`transpose` then `flipud`) give the right orientations. Their only fault is
  the in-place mutation in B1.
