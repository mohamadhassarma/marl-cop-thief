"""Unit tests for strategy module."""

import pytest
from cop_thief.services.grid import Grid, Position
from cop_thief.services.strategy import (
    bfs_shortest_path,
    cop_best_move,
    cop_best_barrier,
    thief_best_move,
    observation_to_positions,
)
from cop_thief.constants import Direction


@pytest.fixture
def grid():
    """Return a clean 5x5 grid."""
    return Grid(5, 5)


class TestBFS:
    """Tests for BFS pathfinding."""

    def test_direct_path(self, grid):
        """BFS finds direct horizontal path."""
        path = bfs_shortest_path(grid, Position(0, 0), Position(0, 3))
        assert len(path) == 3
        assert all(d == Direction.RIGHT for d in path)

    def test_same_position(self, grid):
        """BFS returns empty path when start equals goal."""
        path = bfs_shortest_path(grid, Position(2, 2), Position(2, 2))
        assert path == []

    def test_path_around_barrier(self, grid):
        """BFS routes around a barrier."""
        grid.add_barrier(Position(0, 1))
        path = bfs_shortest_path(grid, Position(0, 0), Position(0, 2))
        assert len(path) > 0
        # Path should not go through (0,1)
        pos = Position(0, 0)
        for d in path:
            from cop_thief.constants import DIRECTION_DELTAS
            dr, dc = DIRECTION_DELTAS[d]
            pos = Position(pos.row + dr, pos.col + dc)
        assert pos == Position(0, 2)

    def test_no_path_when_blocked(self, grid):
        """BFS returns empty list when no path exists."""
        # Surround (0,0) with barriers
        grid.add_barrier(Position(0, 1))
        grid.add_barrier(Position(1, 0))
        path = bfs_shortest_path(grid, Position(0, 0), Position(4, 4))
        assert path == []

    def test_vertical_path(self, grid):
        """BFS finds direct vertical path."""
        path = bfs_shortest_path(grid, Position(0, 0), Position(3, 0))
        assert len(path) == 3
        assert all(d == Direction.DOWN for d in path)

    def test_diagonal_path_length(self, grid):
        """BFS finds optimal path for diagonal target."""
        path = bfs_shortest_path(grid, Position(0, 0), Position(2, 2))
        assert len(path) == 4  # Manhattan distance


class TestCopBestMove:
    """Tests for Cop movement strategy."""

    def test_moves_toward_thief(self, grid):
        """Cop moves in direction of Thief."""
        move = cop_best_move(grid, Position(0, 0), Position(0, 3))
        assert move == Direction.RIGHT

    def test_adjacent_to_thief(self, grid):
        """Cop returns a move even when one step away."""
        move = cop_best_move(grid, Position(0, 0), Position(0, 1))
        assert move == Direction.RIGHT

    def test_no_path_returns_none(self, grid):
        """Returns None when Thief is unreachable."""
        grid.add_barrier(Position(0, 1))
        grid.add_barrier(Position(1, 0))
        move = cop_best_move(grid, Position(0, 0), Position(4, 4))
        assert move is None


class TestCopBestBarrier:
    """Tests for Cop barrier placement strategy."""

    def test_places_barrier_near_thief(self, grid):
        """Barrier placed adjacent to Thief."""
        barrier = cop_best_barrier(grid, Position(0, 0), Position(2, 2), 5)
        assert barrier is not None
        # Should be adjacent to thief
        dist = abs(barrier.row - 2) + abs(barrier.col - 2)
        assert dist == 1

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
        """Thief moves away from Cop."""
        # Cop at (0,0), Thief at (2,2) — should move away (down or right)
        move = thief_best_move(grid, Position(2, 2), Position(0, 0))
        assert move in [Direction.DOWN, Direction.RIGHT]

    def test_avoids_barriers(self, grid):
        """Thief does not move into barrier."""
        grid.add_barrier(Position(2, 3))
        grid.add_barrier(Position(3, 2))
        move = thief_best_move(grid, Position(2, 2), Position(0, 0))
        # Should not suggest moving into a barrier
        from cop_thief.constants import DIRECTION_DELTAS
        dr, dc = DIRECTION_DELTAS[move]
        new_pos = Position(2 + dr, 2 + dc)
        assert not grid.is_barrier(new_pos)

    def test_returns_valid_move_at_corner(self, grid):
        """Thief in corner still returns a valid move."""
        move = thief_best_move(grid, Position(4, 4), Position(0, 0))
        assert move is not None


class TestObservationToPositions:
    """Tests for observation parsing."""

    def test_cop_observation(self):
        """Parses cop observation correctly."""
        obs = {
            "role": "cop",
            "my_position": {"row": 1, "col": 2},
            "opponent_position": {"row": 3, "col": 4},
        }
        my, opp = observation_to_positions(obs)
        assert my == Position(1, 2)
        assert opp == Position(3, 4)

    def test_thief_observation(self):
        """Parses thief observation correctly."""
        obs = {
            "role": "thief",
            "my_position": {"row": 0, "col": 0},
            "cop_last_known": {"row": 4, "col": 4},
        }
        my, opp = observation_to_positions(obs)
        assert my == Position(0, 0)
        assert opp == Position(4, 4)
