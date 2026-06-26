"""Strategy module — BFS pathfinding for Cop, evasion logic for Thief (8-way)."""

from collections import deque

from cop_thief.constants import DIRECTION_DELTAS, Direction
from cop_thief.services.grid import Grid, Position


def bfs_shortest_path(grid: Grid, start: Position, goal: Position) -> list[Direction]:
    """Find shortest path from start to goal using BFS (8-way movement)."""
    if start == goal:
        return []
    queue: deque[tuple[Position, list[Direction]]] = deque()
    queue.append((start, []))
    visited: set[Position] = {start}
    while queue:
        current, path = queue.popleft()
        for direction, (dr, dc) in DIRECTION_DELTAS.items():
            neighbor = Position(current.row + dr, current.col + dc)
            if neighbor in visited:
                continue
            if not grid.is_valid(neighbor):
                continue
            if grid.is_barrier(neighbor):
                continue
            new_path = path + [direction]
            if neighbor == goal:
                return new_path
            visited.add(neighbor)
            queue.append((neighbor, new_path))
    return []


def cop_best_move(grid: Grid, cop_pos: Position, thief_pos: Position) -> Direction | None:
    """Return best move for Cop using BFS (8-way)."""
    path = bfs_shortest_path(grid, cop_pos, thief_pos)
    if path:
        return path[0]
    return None


def cop_best_barrier(
    grid: Grid, cop_pos: Position, thief_pos: Position, barriers_remaining: int
) -> Position | None:
    """Find best barrier position to cut off Thief's escape."""
    if barriers_remaining <= 0:
        return None
    best_pos = None
    best_score = -1
    for _direction, (dr, dc) in DIRECTION_DELTAS.items():
        candidate = Position(thief_pos.row + dr, thief_pos.col + dc)
        if not grid.is_valid(candidate):
            continue
        if grid.is_barrier(candidate):
            continue
        if candidate == cop_pos:
            continue
        dist_from_cop = abs(candidate.row - cop_pos.row) + abs(candidate.col - cop_pos.col)
        if dist_from_cop > best_score:
            best_score = dist_from_cop
            best_pos = candidate
    return best_pos


def thief_best_move(grid: Grid, thief_pos: Position, cop_pos: Position) -> Direction:
    """Return best move for Thief using Chebyshev max-distance evasion."""
    best_dir = None
    best_score = -1
    for direction, (dr, dc) in DIRECTION_DELTAS.items():
        neighbor = Position(thief_pos.row + dr, thief_pos.col + dc)
        if not grid.is_valid(neighbor):
            continue
        if grid.is_barrier(neighbor):
            continue
        dist = max(abs(neighbor.row - cop_pos.row), abs(neighbor.col - cop_pos.col))
        future_options = _count_free_neighbors(grid, neighbor, cop_pos)
        score = dist * 10 + future_options
        if score > best_score:
            best_score = score
            best_dir = direction
    if best_dir is None:
        for direction, (dr, dc) in DIRECTION_DELTAS.items():
            neighbor = Position(thief_pos.row + dr, thief_pos.col + dc)
            if grid.is_valid(neighbor) and not grid.is_barrier(neighbor):
                return direction
    return best_dir or Direction.DOWN


def _count_free_neighbors(grid: Grid, pos: Position, cop_pos: Position) -> int:
    """Count free neighbors — used to avoid dead ends."""
    count = 0
    for _, (dr, dc) in DIRECTION_DELTAS.items():
        neighbor = Position(pos.row + dr, pos.col + dc)
        if grid.is_valid(neighbor) and not grid.is_barrier(neighbor) and neighbor != cop_pos:
            count += 1
    return count


def is_trapped(grid: Grid, pos: Position) -> bool:
    """Check if an agent is completely trapped (no free neighbors)."""
    for _, (dr, dc) in DIRECTION_DELTAS.items():
        neighbor = Position(pos.row + dr, pos.col + dc)
        if grid.is_valid(neighbor) and not grid.is_barrier(neighbor):
            return False
    return True


def observation_to_positions(observation: dict) -> tuple[Position, Position]:
    """Parse agent observation dict into Position objects."""
    my = observation.get("my_position") or observation.get("cop", {})
    opp = (
        observation.get("opponent_position")
        or observation.get("cop_last_known")
        or observation.get("thief", {})
    )
    my_pos = Position(my["row"], my["col"])
    opp_pos = Position(opp["row"], opp["col"])
    return my_pos, opp_pos
