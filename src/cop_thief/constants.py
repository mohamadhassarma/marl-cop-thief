"""Immutable constants and enums for the cop_thief package."""

from enum import Enum


class Direction(str, Enum):
    """Valid movement directions — 8-way King moves."""

    UP = "north"
    DOWN = "south"
    LEFT = "west"
    RIGHT = "east"
    UP_RIGHT = "north-east"
    UP_LEFT = "north-west"
    DOWN_RIGHT = "south-east"
    DOWN_LEFT = "south-west"


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


# 8-way direction vectors: (row_delta, col_delta)
DIRECTION_DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.UP: (-1, 0),
    Direction.DOWN: (1, 0),
    Direction.LEFT: (0, -1),
    Direction.RIGHT: (0, 1),
    Direction.UP_RIGHT: (-1, 1),
    Direction.UP_LEFT: (-1, -1),
    Direction.DOWN_RIGHT: (1, 1),
    Direction.DOWN_LEFT: (1, -1),
}

# Compass word mapping for [INTENT:] messages
COMPASS_WORDS: dict[Direction, str] = {
    Direction.UP: "north",
    Direction.DOWN: "south",
    Direction.LEFT: "west",
    Direction.RIGHT: "east",
    Direction.UP_RIGHT: "north-east",
    Direction.UP_LEFT: "north-west",
    Direction.DOWN_RIGHT: "south-east",
    Direction.DOWN_LEFT: "south-west",
}
