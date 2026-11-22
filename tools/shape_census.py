#!/usr/bin/env python3
"""shape_census.py -- Phase 1 analysis of the 73 starter ExTetromino matrices.

Read-only with respect to the reference starter code: it loads
../allextetrominoes.py by path (no bytecode written) and never modifies it.

What it computes
  1. Normalises every matrix (trim empty border rows/cols) and deduplicates
       a) exactly (fixed orientation),
       b) under rotation only        (one-sided classes),
       c) under rotation + reflection (free classes).
  2. Groups distinct shapes by unordered bounding box and by connectivity
     (edge-connected = classic tetromino; corner-connected = needs a diagonal).
  3. For every distinct one-sided shape and each of its distinct rotations,
     the flat-floor hole count: in each column of the piece, the number of
     empty cells that lie below the column's topmost filled cell, when the
     piece rests with its bounding-box bottom on a flat floor.
  4. Enumerates *all* 4-cell king-connected (8-neighbour) shapes from scratch
     and checks whether the starter set is exhaustive.

Usage
  python3 tools/shape_census.py            # print summary to stdout
  python3 tools/shape_census.py --write    # also write docs/generated/*.md/json

Dependencies: Python 3 + numpy only.
"""
import argparse
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True  # keep the reference folder untouched

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "allextetrominoes.py"
N_STARTER = 73


# ---------------------------------------------------------------- loading ---
def load_reference_matrices():
    spec = importlib.util.spec_from_file_location("_ref_allextetrominoes", REFERENCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {i: np.array(getattr(mod, f"Extetromino{i}"), dtype=bool).copy()
            for i in range(1, N_STARTER + 1)}


# ------------------------------------------------------- shape primitives ---
def trim(m):
    m = np.asarray(m, dtype=bool)
    rows = np.where(m.any(axis=1))[0]
    cols = np.where(m.any(axis=0))[0]
    return m[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]


def key(m):
    """Hashable, orderable representation of a (trimmed) matrix."""
    m = trim(m)
    return (m.shape, tuple(int(v) for v in m.flatten()))


def from_key(k):
    shape, flat = k
    return np.array(flat, dtype=bool).reshape(shape)


def rotations(m):
    """The 4 rotations, clockwise order starting from the given orientation."""
    return [trim(np.rot90(m, -k)) for k in range(4)]


def distinct_rotations(m):
    seen, out = set(), []
    for r in rotations(m):
        k = key(r)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def one_sided_key(m):
    return min(key(r) for r in rotations(m))


def free_key(m):
    return min(one_sided_key(m), one_sided_key(np.fliplr(m)))


def cells(m):
    return {(int(r), int(c)) for r, c in zip(*np.nonzero(m))}


def is_connected(m, diagonal):
    cs = cells(m)
    if not cs:
        return False
    steps = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        steps += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    start = next(iter(cs))
    stack, seen = [start], {start}
    while stack:
        r, c = stack.pop()
        for dr, dc in steps:
            n = (r + dr, c + dc)
            if n in cs and n not in seen:
                seen.add(n)
                stack.append(n)
    return seen == cs


def connectivity(m):
    if is_connected(m, diagonal=False):
        return "edge"
    if is_connected(m, diagonal=True):
        return "corner"
    return "disconnected"


def bbox_label(m):
    h, w = trim(m).shape
    a, b = max(h, w), min(h, w)
    return f"{a}x{b}"


def hole_profile(m):
    """Per-column flat-floor holes: empty cells below the topmost filled cell."""
    m = trim(m)
    prof = []
    for c in range(m.shape[1]):
        col = m[:, c]
        top = int(np.argmax(col))  # first True from the top
        prof.append(int((~col[top:]).sum()))
    return tuple(prof)


def render(m, on="█", off="·"):
    return "\n".join("".join(on if v else off for v in row) for row in trim(m))


def render_side_by_side(ms, gap="   "):
    blocks = [render(m).split("\n") for m in ms]
    h = max(len(b) for b in blocks)
    widths = [len(b[0]) for b in blocks]
    lines = []
    for i in range(h):
        lines.append(gap.join((b[i] if i < len(b) else " " * w)
                              for b, w in zip(blocks, widths)).rstrip())
    return "\n".join(lines)


# ------------------------------------------------------ full enumeration ---
def enumerate_king_tetrominoes():
    """All fixed 4-cell shapes connected through edges or corners."""
    nbrs = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]
    frontier = {frozenset({(0, 0)})}
    for _ in range(3):
        nxt = set()
        for s in frontier:
            for (r, c) in s:
                for dr, dc in nbrs:
                    n = (r + dr, c + dc)
                    if n not in s:
                        nxt.add(frozenset(s | {n}))
        frontier = nxt
    fixed = set()
    for s in frontier:
        r0 = min(r for r, _ in s)
        c0 = min(c for _, c in s)
        h = max(r for r, _ in s) - r0 + 1
        w = max(c for _, c in s) - c0 + 1
        m = np.zeros((h, w), dtype=bool)
        for r, c in s:
            m[r - r0, c - c0] = True
        fixed.add(key(m))
    return fixed


# ---------------------------------------------------------------- census ---
def census():
    mats = load_reference_matrices()

    # sanity checks on raw input
    sanity = {}
    for i, m in mats.items():
        sanity[i] = {
            "cells": int(m.sum()),
            "tight_bbox": trim(m).shape == m.shape,
            "connectivity": connectivity(m),
        }

    # (a) exact duplicates
    exact = defaultdict(list)
    for i, m in mats.items():
        exact[key(m)].append(i)

    # (b) one-sided, (c) free
    one_sided = defaultdict(list)
    free = defaultdict(list)
    for i, m in mats.items():
        one_sided[one_sided_key(m)].append(i)
        free[free_key(m)].append(i)

    # exhaustive comparison
    all_fixed = enumerate_king_tetrominoes()
    all_one_sided = {one_sided_key(from_key(k)) for k in all_fixed}
    all_free = {free_key(from_key(k)) for k in all_fixed}
    starter_fixed = set(exact)
    missing_one_sided = sorted(all_one_sided - set(one_sided))
    missing_free = sorted(all_free - set(free))

    # per one-sided class details
    classes = []
    for n, (osk, idxs) in enumerate(sorted(one_sided.items(),
                                           key=lambda kv: (min(kv[1]),)), start=1):
        m = from_key(osk)
        # use the first starter matrix's orientation as the "spawn" orientation
        spawn = trim(mats[min(idxs)])
        rots = distinct_rotations(spawn)
        orient = []
        for r in rots:
            hp = hole_profile(r)
            orient.append({
                "matrix": render(r),
                "dims_hxw": list(r.shape),
                "hole_profile": list(hp),
                "holes": int(sum(hp)),
                "in_starter_as": sorted(exact.get(key(r), [])),
            })
        fk = free_key(m)
        mirror_os = one_sided_key(np.fliplr(m))
        classes.append({
            "id": f"S{n:02d}",
            "starter_indices": sorted(idxs),
            "free_class": fk,
            "bbox": bbox_label(m),
            "connectivity": connectivity(m),
            "chiral": mirror_os != osk,
            "mirror_in_starter": mirror_os in one_sided,
            "n_rotations": len(rots),
            "orientations": orient,
            "min_holes": min(o["holes"] for o in orient),
            "max_holes": max(o["holes"] for o in orient),
            "_rot_mats": rots,
        })

    # free-class ids
    free_ids = {}
    for c in classes:
        free_ids.setdefault(c["free_class"], f"F{len(free_ids) + 1:02d}")
        c["free_id"] = free_ids[c["free_class"]]

    return {
        "mats": mats,
        "sanity": sanity,
        "exact": exact,
        "one_sided": one_sided,
        "free": free,
        "classes": classes,
        "all_fixed": all_fixed,
        "all_one_sided": all_one_sided,
        "all_free": all_free,
        "starter_fixed": starter_fixed,
        "missing_one_sided": missing_one_sided,
        "missing_free": missing_free,
    }


# --------------------------------------------------------------- reports ---
def summary_lines(r):
    s = r["sanity"]
    bad = [i for i, v in s.items() if v["cells"] != 4 or not v["tight_bbox"]
           or v["connectivity"] == "disconnected"]
    dup_exact = [v for v in r["exact"].values() if len(v) > 1]
    yield f"matrices loaded                       : {len(r['mats'])}"
    yield f"malformed (not 4 cells / loose bbox / disconnected): {bad or 'none'}"
    yield f"distinct fixed orientations           : {len(r['exact'])}"
    yield f"exact duplicates                      : {dup_exact}"
    yield f"distinct under rotation (one-sided)   : {len(r['one_sided'])}"
    yield f"distinct under rotation + reflection  : {len(r['free'])}"
    yield ""
    yield ("all 4-cell edge-or-corner-connected shapes: "
           f"{len(r['all_fixed'])} fixed, {len(r['all_one_sided'])} one-sided, "
           f"{len(r['all_free'])} free")
    yield (f"starter covers {len(r['starter_fixed'])}/{len(r['all_fixed'])} fixed, "
           f"{len(r['one_sided'])}/{len(r['all_one_sided'])} one-sided, "
           f"{len(r['free'])}/{len(r['all_free'])} free")
    yield f"one-sided classes missing from starter: {len(r['missing_one_sided'])}"
    yield f"free classes missing from starter     : {len(r['missing_free'])}"


def markdown(r):
    out = []
    w = out.append
    w("# Shape census (generated)\n")
    w("Generated by `tools/shape_census.py --write`. Do not edit by hand.\n")
    w("```text")
    out.extend(summary_lines(r))
    w("```\n")

    # Exhaustiveness
    w("## Shapes absent from the starter set\n")
    if r["missing_one_sided"]:
        w("One-sided classes (rotation-distinct) that never appear in "
          "`allextetrominoes.py` in any orientation:\n")
        w("```text")
        w(render_side_by_side([from_key(k) for k in r["missing_one_sided"]]))
        w("```\n")
    else:
        w("None: every one-sided class appears at least once.\n")

    # grouping tables
    classes = r["classes"]
    w("## Grouping of the one-sided classes\n")
    groups = defaultdict(list)
    for c in classes:
        groups[(c["bbox"], c["connectivity"])].append(c["id"])
    w("| bounding box | edge-connected | corner-connected | total |")
    w("|---|---|---|---|")
    for bb in sorted({c["bbox"] for c in classes},
                     key=lambda s: tuple(map(int, s.split("x")))):
        e = groups.get((bb, "edge"), [])
        k = groups.get((bb, "corner"), [])
        w(f"| {bb} | {len(e)} ({', '.join(e) or '-'}) | "
          f"{len(k)} ({', '.join(k) or '-'}) | {len(e) + len(k)} |")
    w(f"| **all** | {sum(c['connectivity'] == 'edge' for c in classes)} | "
      f"{sum(c['connectivity'] == 'corner' for c in classes)} | {len(classes)} |\n")

    fgroups = defaultdict(set)
    for c in classes:
        fgroups[(c["bbox"], c["connectivity"])].add(c["free_id"])
    w("Same grouping, counted as free classes (rotation + reflection):\n")
    w("| bounding box | edge-connected | corner-connected | total |")
    w("|---|---|---|---|")
    for bb in sorted({c["bbox"] for c in classes},
                     key=lambda s: tuple(map(int, s.split("x")))):
        e = fgroups.get((bb, "edge"), set())
        k = fgroups.get((bb, "corner"), set())
        w(f"| {bb} | {len(e)} | {len(k)} | {len(e) + len(k)} |")
    w(f"| **all** | {len({c['free_id'] for c in classes if c['connectivity'] == 'edge'})} | "
      f"{len({c['free_id'] for c in classes if c['connectivity'] == 'corner'})} | "
      f"{len({c['free_id'] for c in classes})} |\n")

    # per-class detail
    w("## Per-shape detail: orientations and flat-floor holes\n")
    w("Hole rule: piece rests with the bottom of its bounding box on a flat "
      "floor; in each column, count empty cells below that column's topmost "
      "filled cell. `profile` lists the per-column counts left to right. "
      "Orientations are clockwise rotations of the starter's first listed "
      "orientation, duplicates removed.\n")
    w("| id | free | starter indices | bbox | conn. | chiral | mirror in starter | "
      "#rot | holes per rotation | min | max |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for c in classes:
        hs = " / ".join(str(o["holes"]) for o in c["orientations"])
        w(f"| {c['id']} | {c['free_id']} | {', '.join(map(str, c['starter_indices']))} | "
          f"{c['bbox']} | {c['connectivity']} | {'yes' if c['chiral'] else 'no'} | "
          f"{('yes' if c['mirror_in_starter'] else 'NO') if c['chiral'] else '-'} | "
          f"{c['n_rotations']} | {hs} | {c['min_holes']} | {c['max_holes']} |")
    w("")
    for c in classes:
        w(f"### {c['id']}  (free {c['free_id']}; starter "
          f"#{', #'.join(map(str, c['starter_indices']))}; {c['bbox']}, "
          f"{c['connectivity']}-connected)\n")
        w("```text")
        w(render_side_by_side(c["_rot_mats"]))
        w("```")
        w("| rot | h x w | hole profile | holes | starter index of this orientation |")
        w("|---|---|---|---|---|")
        for k, o in enumerate(c["orientations"]):
            w(f"| {k * 90}° CW | {o['dims_hxw'][0]}x{o['dims_hxw'][1]} | "
              f"{tuple(o['hole_profile'])} | {o['holes']} | "
              f"{', '.join(map(str, o['in_starter_as'])) or '-'} |")
        w("")

    # hole-profile histogram
    w("## Distribution of minimum flat-floor holes\n")
    hist = defaultdict(list)
    for c in classes:
        hist[c["min_holes"]].append(c["id"])
    w("| min holes over rotations | # one-sided classes | classes |")
    w("|---|---|---|")
    for h in sorted(hist):
        w(f"| {h} | {len(hist[h])} | {', '.join(hist[h])} |")
    w("")
    return "\n".join(out)


def to_json(r):
    return {
        "summary": list(summary_lines(r)),
        "exact_duplicates": [v for v in r["exact"].values() if len(v) > 1],
        "classes": [{k: v for k, v in c.items()
                     if not k.startswith("_") and k != "free_class"}
                    for c in r["classes"]],
        "missing_one_sided": [render(from_key(k)) for k in r["missing_one_sided"]],
        "missing_free": [render(from_key(k)) for k in r["missing_free"]],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true",
                    help="write docs/generated/shape_census.{md,json}")
    args = ap.parse_args()
    r = census()
    for line in summary_lines(r):
        print(line)
    if args.write:
        outdir = ROOT / "docs" / "generated"
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "shape_census.md").write_text(markdown(r), encoding="utf-8")
        (outdir / "shape_census.json").write_text(json.dumps(to_json(r), indent=2),
                                                  encoding="utf-8")
        print(f"\nwrote {outdir / 'shape_census.md'} and shape_census.json")


if __name__ == "__main__":
    main()
