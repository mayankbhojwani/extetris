"""extetris: an extended-Tetris engine.

The window (extetris.window.GameWindow) is not imported here, so the rest
can be used without tkinter.
"""
from .board import Board
from .game import Game, any_piece
from .generator import PieceGenerator
from .mixes import (MODES, STYLES, BoardAwareMix, PieceMix, assistive, fair, mix,
                     mode, only, progressive, unfair)
from .pieces import (DIFFICULTY_CLASSES, ExTetromino, FourHole, NoHole,
                     OneHole, PieceInfo, SixHole, ThreeHole, TwoHole)
from .shape import Shape

__all__ = [
    "Game", "any_piece", "Board",
    "PieceMix", "mix", "only", "progressive", "mode", "MODES",
    "BoardAwareMix", "fair", "assistive", "unfair", "STYLES",
    "Shape", "ExTetromino", "PieceInfo", "PieceGenerator", "DIFFICULTY_CLASSES",
    "NoHole", "OneHole", "TwoHole", "ThreeHole", "FourHole", "SixHole",
]
