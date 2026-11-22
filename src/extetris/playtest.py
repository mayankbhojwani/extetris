"""Playtest robot: plays a variant automatically to estimate how hard it is.

The robot looks at every turn and column for the falling piece and picks the
landing spot that keeps the board lowest and tidiest. It uses a well-known
simple scoring rule: fewer holes, lower and flatter stacks, more cleared
lines. It is not a perfect player, but the same robot on two variants shows
which one is harder.

    from extetris.playtest import playtest
    report = playtest(variant, games=5, max_pieces=250)
"""
import random
from collections import Counter

import numpy as np

# Weights of the scoring rule (from a widely used simple Tetris AI).
HEIGHT_W, LINES_W, HOLES_W, BUMPY_W = -0.51, 0.76, -0.36, -0.18


def _column_heights(cells):
    h = cells.shape[0]
    filled = cells.any(axis=0)
    first = np.argmax(cells, axis=0)
    return np.where(filled, h - first, 0)


def score_board(board, lines_cleared):
    """Higher is better for the robot."""
    heights = _column_heights(board.cells)
    bumpiness = int(np.abs(np.diff(heights)).sum())
    return (HEIGHT_W * int(heights.sum()) + LINES_W * lines_cleared
            + HOLES_W * board.holes() + BUMPY_W * bumpiness)


def best_move(game):
    """(turn, column) the robot would choose for the falling piece, or None."""
    best, best_score = None, None
    turn = game.piece
    seen = set()
    for _ in range(4):
        key = turn.matrix.tobytes() + bytes(turn.matrix.shape)
        if key not in seen:
            seen.add(key)
            for col in range(game.width - turn.width + 1):
                row = game.board.drop_row(turn, col)
                if row is None:
                    continue
                after, cleared = game.board.place(turn, row, col).clear_full_rows()
                s = score_board(after, cleared)
                if best_score is None or s > best_score:
                    best, best_score = (turn, col), s
        turn = turn.rotated_cw()
    return best


def autoplay(game, max_pieces=250):
    """Let the robot play `game` until game over or `max_pieces` pieces.

    Returns a Counter of the difficulty classes it was given.
    """
    seen = Counter()
    while not game.game_over and game.pieces_placed < max_pieces:
        seen[type(game.piece).__name__] += 1
        move = best_move(game)
        if move is None or not game.drop_at(*move):
            game.game_over = True      # nowhere to put it: the stack is full
    return seen


def playtest(variant, games=5, max_pieces=250, seed=0):
    """Play `games` robot games of a Variant and summarise them.

    Returns a dict with average lines and pieces, how many games ended by
    reaching the top, and the share of each difficulty class actually seen.
    """
    rng = random.Random(seed)
    lines, pieces, topped = [], [], 0
    seen = Counter()
    for _ in range(games):
        g = variant.make_game(rng=random.Random(rng.random()))
        seen += autoplay(g, max_pieces)
        lines.append(g.lines)
        pieces.append(g.pieces_placed)
        topped += g.game_over
    total = sum(seen.values()) or 1
    return {
        "games": games,
        "max_pieces": max_pieces,
        "average_lines": sum(lines) / games,
        "average_pieces": sum(pieces) / games,
        "topped_out": topped,
        "class_share": {k: v / total for k, v in seen.items()},
    }


def summary(report):
    """The playtest report as a few plain sentences."""
    shares = ", ".join(f"{k} {v:.0%}" for k, v in
                       sorted(report["class_share"].items(), key=lambda kv: -kv[1]))
    return (f"Robot playtest: {report['games']} games, up to "
            f"{report['max_pieces']} pieces each.\n"
            f"Average lines cleared: {report['average_lines']:.1f}\n"
            f"Average pieces placed: {report['average_pieces']:.1f}\n"
            f"Games that reached the top: {report['topped_out']} of {report['games']}\n"
            f"Pieces seen: {shares}")
