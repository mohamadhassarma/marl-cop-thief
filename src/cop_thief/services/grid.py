"""Grid — manages the 2D game board, positions, and barriers."""

from dataclasses import dataclass, field
from cop_thief.constants import Direction, DIRECTION_DELTAS


@dataclass
class Position:
    """A cell position on the grid."""

    row: int
    col: int

    def __eq__(self, other: object) -> bool:
        """Check position equality."""
        if not isinstance(other, Position):
            return False
        return self.row == other.row and self.col == other.col

    def __hash__(self) -> int:
        """Make Position hashable for use in sets/dicts."""
        return hash((self.row, self.col))

    def __repr__(self) -> str:
        """Human-readable position string."""
        return f"({self.row},{self.col})"


class Grid:
    """Manages the game board state: bounds, barriers, and movement.

    The grid is 0-indexed. (0,0) is top-left.
    Barriers block movement into a cell but do not block the Cop.
    """

    def __init__(self, rows: int, cols: int) -> None:
        """Initialize an empty grid.

        Args:
            rows: Number of rows.
            cols: Number of columns.

        Raises:
            ValueError: If dimensions are less than 2.
        """
        if rows < 2 or cols < 2:
            raise ValueError("Grid must be at least 2x2")
        self.rows = rows
        self.cols = cols
        self._barriers: set[Position] = field(default_factory=set)
        self._barriers = set()

    def is_valid(self, pos: Position) -> bool:
        """Return True if position is within grid bounds."""
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols

    def is_barrier(self, pos: Position) -> bool:
        """Return True if a barrier exists at the given position."""
        return pos in self._barriers

    def add_barrier(self, pos: Position) -> None:
        """Place a barrier at the given position.

        Args:
            pos: Target cell for barrier.

        Raises:
            ValueError: If position is out of bounds.
        """
        if not self.is_valid(pos):
            raise ValueError(f"Cannot place barrier outside grid: {pos}")
        self._barriers.add(pos)

    def get_barriers(self) -> set[Position]:
        """Return a copy of all current barrier positions."""
        return set(self._barriers)

    def barrier_count(self) -> int:
        """Return number of barriers currently on the grid."""
        return len(self._barriers)

    def apply_move(self, pos: Position, direction: Direction) -> Position:
        """Compute new position after a move, respecting bounds and barriers.

        Args:
            pos: Current position.
            direction: Direction to move.

        Returns:
            New position if valid, original position if blocked.
        """
        delta = DIRECTION_DELTAS[direction]
        new_pos = Position(pos.row + delta[0], pos.col + delta[1])
        if not self.is_valid(new_pos) or self.is_barrier(new_pos):
            return pos
        return new_pos

    def reset_barriers(self) -> None:
        """Remove all barriers — called at start of each sub-game."""
        self._barriers.clear()

    def render(self, cop_pos: Position, thief_pos: Position) -> str:
        """Return ASCII representation of the grid.

        Args:
            cop_pos: Current Cop position.
            thief_pos: Current Thief position.

        Returns:
            Multi-line string grid visualization.
        """
        lines = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                p = Position(r, c)
                if p == cop_pos and p == thief_pos:
                    row.append("X")  # Both on same cell = capture
                elif p == cop_pos:
                    row.append("C")
                elif p == thief_pos:
                    row.append("T")
                elif self.is_barrier(p):
                    row.append("#")
                else:
                    row.append(".")
            lines.append(" ".join(row))
        return "\n".join(lines)
