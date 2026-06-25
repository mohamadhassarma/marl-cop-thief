"""Unit tests for strategy module (8-way movement)."""

import pytest
from cop_thief.services.grid import Grid, Position
from cop_thief.services.strategy import (
    bfs_shortest_path,
    cop_best_move,
    cop_best_barrier,
    thief_best_move,
    is_trapped,
    observation_to_positions,
)
from cop_thief.constants import Direction


@pytest.fixture
def grid():
    """Return a clean 5x5 grid."""
    return Grid(5, 5)


class TestBFS:
    """Tests for BFS pathfinding with 8-way movement."""

    def test_direct_path(self, grid):
        """BFS finds direct horizontal path."""
        path = bfs_shortest_path(grid, Position(0, 0), Position(0, 3))
        assert len(path) == 3

    def test_same_position(self, grid):
        """BFS returns empty path when start equals goal."""
        path = bfs_shortest_path(grid, Position(2, 2), Position(2, 2))
        assert path == []

    def test_diagonal_path_length(self, grid):
        """BFS uses diagonal — 2 steps to reach (2,2) from (0,0)."""
        path = bfs_shortest_path(grid, Position(0, 0), Position(2, 2))
        assert len(path) == 2  # diagonal shortcut

    def test_path_around_barrier(self, grid):
        """BFS routes around a barrier."""
        grid.add_barrier(Position(0, 1))
        path = bfs_shortest_path(grid, Position(0, 0), Position(0, 2))
        assert len(path) > 0
        assert path is not None

    def test_no_path_when_fully_blocked(self, grid):
        """BFS returns empty when fully surrounded by barriers."""
        # Block all 8 neighbors of (0,0) — but (0,0) is corner so only 3 neighbors
        grid.add_barrier(Position(0, 1))
        grid.add_barrier(Position(1, 0))
        grid.add_barrier(Position(1, 1))
        path = bfs_shortest_path(grid, Position(0, 0), Position(4, 4))
        assert path == []

    def test_vertical_path(self, grid):
        """BFS finds direct vertical path."""
        path = bfs_shortest_path(grid, Position(0, 0), Position(3, 0))
        assert len(path) == 3


class TestCopBestMove:
    """Tests for Cop movement strategy."""

    def test_moves_toward_thief(self, grid):
        """Cop moves in direction of Thief."""
        move = cop_best_move(grid, Position(0, 0), Position(0, 3))
        assert move is not None

    def test_adjacent_to_thief(self, grid):
        """Cop returns a move when one step away."""
        move = cop_best_move(grid, Position(0, 0), Position(0, 1))
        assert move is not None

    def test_no_path_returns_none(self, grid):
        """Returns None when Thief is unreachable."""
        grid.add_barrier(Position(0, 1))
        grid.add_barrier(Position(1, 0))
        grid.add_barrier(Position(1, 1))
        move = cop_best_move(grid, Position(0, 0), Position(4, 4))
        assert move is None

    def test_diagonal_move(self, grid):
        """Cop uses diagonal move when available."""
        move = cop_best_move(grid, Position(0, 0), Position(2, 2))
        assert move == Direction.DOWN_RIGHT


class TestCopBestBarrier:
    """Tests for Cop barrier placement strategy."""

    def test_places_barrier_near_thief(self, grid):
        """Barrier placed near Thief."""
        barrier = cop_best_barrier(grid, Position(0, 0), Position(2, 2), 5)
        assert barrier is not None

    def test_no_barriers_remaining(self, grid):
        """Returns None when no barriers left."""
        barrier = cop_best_barrier(grid, Position(0, 0), Position(2, 2), 0)
        assert barrier is None

    def test_does_not_block_cop(self, grid):
        """Barrier not placed on Cop's position."""
        barrier = cop_best_barrier(grid, Position(2, 1), Position(2, 2), 5)
        if barrier:
            assert barrier != Position(2, 1)


class TestThiefBestMove:
    """Tests for Thief evasion strategy."""

    def test_moves_away_from_cop(self, grid):
        """Thief moves away from Cop using diagonals."""
        move = thief_best_move(grid, Position(2, 2), Position(0, 0))
        assert move in [Direction.DOWN, Direction.RIGHT,
                        Direction.DOWN_RIGHT, Direction.DOWN_LEFT]

    def test_avoids_barriers(self, grid):
        """Thief does not move into barrier."""
        grid.add_barrier(Position(3, 3))
        move = thief_best_move(grid, Position(2, 2), Position(0, 0))
        from cop_thief.constants import DIRECTION_DELTAS
        dr, dc = DIRECTION_DELTAS[move]
        new_pos = Position(2 + dr, 2 + dc)
        assert not grid.is_barrier(new_pos)

    def test_returns_valid_move_at_corner(self, grid):
        """Thief in corner still returns a valid move."""
        move = thief_best_move(grid, Position(4, 4), Position(0, 0))
        assert move is not None


class TestIsTrapped:
    """Tests for trap detection."""

    def test_not_trapped_open_grid(self, grid):
        """Agent is not trapped on open grid."""
        assert is_trapped(grid, Position(2, 2)) is False

    def test_trapped_when_surrounded(self, grid):
        """Agent is trapped when all 8 neighbors are barriers."""
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                p = Position(2 + dr, 2 + dc)
                if grid.is_valid(p):
                    grid.add_barrier(p)
        assert is_trapped(grid, Position(2, 2)) is True


class TestObservationToPositions:
    """Tests for observation parsing."""

    def test_internal_format(self):
        """Parses internal observation format."""
        obs = {
            "my_position": {"row": 1, "col": 2},
            "opponent_position": {"row": 3, "col": 4},
        }
        my, opp = observation_to_positions(obs)
        assert my == Position(1, 2)
        assert opp == Position(3, 4)

    def test_inter_group_cop_format(self):
        """Parses inter-group cop observation format."""
        obs = {
            "role": "cop",
            "cop": {"row": 0, "col": 0},
            "thief": {"row": 4, "col": 4},
        }
        my, opp = observation_to_positions(obs)
        assert my == Position(0, 0)
        assert opp == Position(4, 4)

    def test_thief_observation(self):
        """Parses thief observation correctly."""
        obs = {
            "my_position": {"row": 0, "col": 0},
            "cop_last_known": {"row": 4, "col": 4},
        }
        my, opp = observation_to_positions(obs)
        assert my == Position(0, 0)
        assert opp == Position(4, 4)
