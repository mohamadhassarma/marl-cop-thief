"""Unit tests for the Grid and Position classes."""

import pytest
from cop_thief.services.grid import Grid, Position
from cop_thief.constants import Direction


class TestPosition:
    """Tests for Position dataclass."""

    def test_equality(self):
        """Two positions with same coords are equal."""
        assert Position(1, 2) == Position(1, 2)

    def test_inequality(self):
        """Positions with different coords are not equal."""
        assert Position(1, 2) != Position(2, 1)

    def test_hashable(self):
        """Position can be used in a set."""
        s = {Position(0, 0), Position(0, 1), Position(0, 0)}
        assert len(s) == 2

    def test_repr(self):
        """Position repr is human-readable."""
        assert repr(Position(3, 4)) == "(3,4)"


class TestGridInit:
    """Tests for Grid initialization."""

    def test_valid_init(self):
        """Grid initializes with valid dimensions."""
        g = Grid(5, 5)
        assert g.rows == 5
        assert g.cols == 5

    def test_too_small(self):
        """Grid raises ValueError if dimensions < 2."""
        with pytest.raises(ValueError):
            Grid(1, 5)
        with pytest.raises(ValueError):
            Grid(5, 1)


class TestGridBounds:
    """Tests for position validity checks."""

    def setup_method(self):
        """Create a 5x5 grid for each test."""
        self.grid = Grid(5, 5)

    def test_valid_position(self):
        """Center position is valid."""
        assert self.grid.is_valid(Position(2, 2))

    def test_top_left_valid(self):
        """Top-left corner is valid."""
        assert self.grid.is_valid(Position(0, 0))

    def test_bottom_right_valid(self):
        """Bottom-right corner is valid."""
        assert self.grid.is_valid(Position(4, 4))

    def test_out_of_bounds_row(self):
        """Row out of bounds is invalid."""
        assert not self.grid.is_valid(Position(5, 0))

    def test_out_of_bounds_col(self):
        """Col out of bounds is invalid."""
        assert not self.grid.is_valid(Position(0, 5))

    def test_negative_position(self):
        """Negative coordinates are invalid."""
        assert not self.grid.is_valid(Position(-1, 0))


class TestBarriers:
    """Tests for barrier placement and detection."""

    def setup_method(self):
        """Create a 5x5 grid for each test."""
        self.grid = Grid(5, 5)

    def test_add_barrier(self):
        """Barrier is detected after placement."""
        self.grid.add_barrier(Position(2, 2))
        assert self.grid.is_barrier(Position(2, 2))

    def test_no_barrier_initially(self):
        """No barriers exist on fresh grid."""
        assert not self.grid.is_barrier(Position(0, 0))

    def test_barrier_count(self):
        """Barrier count increments correctly."""
        self.grid.add_barrier(Position(1, 1))
        self.grid.add_barrier(Position(2, 2))
        assert self.grid.barrier_count() == 2

    def test_barrier_out_of_bounds(self):
        """Placing barrier outside grid raises ValueError."""
        with pytest.raises(ValueError):
            self.grid.add_barrier(Position(10, 10))

    def test_reset_barriers(self):
        """Reset clears all barriers."""
        self.grid.add_barrier(Position(1, 1))
        self.grid.reset_barriers()
        assert self.grid.barrier_count() == 0


class TestMovement:
    """Tests for apply_move method."""

    def setup_method(self):
        """Create a 5x5 grid for each test."""
        self.grid = Grid(5, 5)

    def test_move_down(self):
        """Moving down increases row by 1."""
        new = self.grid.apply_move(Position(0, 0), Direction.DOWN)
        assert new == Position(1, 0)

    def test_move_right(self):
        """Moving right increases col by 1."""
        new = self.grid.apply_move(Position(0, 0), Direction.RIGHT)
        assert new == Position(0, 1)

    def test_move_up(self):
        """Moving up decreases row by 1."""
        new = self.grid.apply_move(Position(2, 2), Direction.UP)
        assert new == Position(1, 2)

    def test_move_left(self):
        """Moving left decreases col by 1."""
        new = self.grid.apply_move(Position(2, 2), Direction.LEFT)
        assert new == Position(2, 1)

    def test_blocked_by_wall(self):
        """Moving into wall returns original position."""
        pos = Position(0, 0)
        assert self.grid.apply_move(pos, Direction.UP) == pos
        assert self.grid.apply_move(pos, Direction.LEFT) == pos

    def test_blocked_by_barrier(self):
        """Moving into barrier returns original position."""
        self.grid.add_barrier(Position(1, 0))
        pos = Position(0, 0)
        assert self.grid.apply_move(pos, Direction.DOWN) == pos


class TestRender:
    """Tests for ASCII grid rendering."""

    def test_render_basic(self):
        """Render shows C for cop and T for thief."""
        grid = Grid(3, 3)
        output = grid.render(Position(0, 0), Position(2, 2))
        assert "C" in output
        assert "T" in output

    def test_render_capture(self):
        """Render shows X when both agents on same cell."""
        grid = Grid(3, 3)
        output = grid.render(Position(1, 1), Position(1, 1))
        assert "X" in output

    def test_render_barrier(self):
        """Render shows # for barriers."""
        grid = Grid(3, 3)
        grid.add_barrier(Position(1, 1))
        output = grid.render(Position(0, 0), Position(2, 2))
        assert "#" in output
