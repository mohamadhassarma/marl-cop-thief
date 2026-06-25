"""Immutable constants and enums for the cop_thief package."""

from enum import Enum


class Direction(str, Enum):
    """Valid movement directions for agents."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class Role(str, Enum):
    """Agent roles in the game."""

    COP = "cop"
    THIEF = "thief"


class SubGameResult(str, Enum):
    """Possible outcomes of a sub-game."""

    COP_WIN = "cop_win"
    THIEF_WIN = "thief_win"


class ActionType(str, Enum):
    """Types of actions an agent can take."""

    MOVE = "move"
    PLACE_BARRIER = "place_barrier"


# Direction vectors: (row_delta, col_delta)
DIRECTION_DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.UP: (-1, 0),
    Direction.DOWN: (1, 0),
    Direction.LEFT: (0, -1),
    Direction.RIGHT: (0, 1),
}
