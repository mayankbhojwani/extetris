"""extetris: an extended-Tetris engine (so far: pieces and the board)."""
from .board import Board
from .generator import PieceGenerator
from .pieces import (DIFFICULTY_CLASSES, ExTetromino, FourHole, NoHole,
                     OneHole, PieceInfo, SixHole, ThreeHole, TwoHole)
from .shape import Shape

__all__ = [
    "Board", "Shape", "ExTetromino", "PieceInfo", "PieceGenerator", "DIFFICULTY_CLASSES",
    "NoHole", "OneHole", "TwoHole", "ThreeHole", "FourHole", "SixHole",
]
