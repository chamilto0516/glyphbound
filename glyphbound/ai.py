from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from .dungeon import Dungeon
    from .monsters import Monster

from .dungeon import FLOOR, DOOR_OPEN, STAIR_DOWN, STAIR_UP


def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Calculate Manhattan distance between two points."""
    return abs(x1 - x2) + abs(y1 - y2)


def is_walkable(dungeon: Dungeon, x: int, y: int) -> bool:
    """Check if a tile is walkable (floor, open door, stairs) and unoccupied."""
    tile = dungeon.tile_at(x, y)
    if tile not in (FLOOR, DOOR_OPEN, STAIR_DOWN, STAIR_UP):
        return False
    # Check if another monster is there
    if dungeon.monster_at(x, y) is not None:
        return False
    # Check if player is there (don't block attack opportunities)
    if (x, y) == (dungeon.party_x, dungeon.party_y):
        return True  # allow moving adjacent for attack
    return True


def get_neighbors(x: int, y: int) -> list[Tuple[int, int]]:
    """Get 4-directional neighbors (no diagonals for simplicity)."""
    return [
        (x, y - 1),  # north
        (x, y + 1),  # south
        (x - 1, y),  # west
        (x + 1, y),  # east
    ]


def simple_chase(dungeon: Dungeon, monster_x: int, monster_y: int, target_x: int, target_y: int) -> Optional[Tuple[int, int]]:
    """
    Simple greedy pathfinding: move toward target by reducing Manhattan distance.
    Returns (new_x, new_y) or None if can't move closer.
    """
    current_dist = manhattan_distance(monster_x, monster_y, target_x, target_y)
    neighbors = get_neighbors(monster_x, monster_y)
    random.shuffle(neighbors)  # randomize tie-breaking

    best_move = None
    best_dist = current_dist

    for nx, ny in neighbors:
        if not is_walkable(dungeon, nx, ny):
            continue
        dist = manhattan_distance(nx, ny, target_x, target_y)
        if dist < best_dist:
            best_dist = dist
            best_move = (nx, ny)

    return best_move


def ai_turn(dungeon: Dungeon, monster: Monster, mx: int, my: int) -> Optional[Tuple[int, int]]:
    """
    Execute one AI turn for a monster at (mx, my).
    Returns (new_x, new_y) if monster moves, or None if it stays put.
    Does NOT handle combat — caller checks if new position collides with player.
    """
    from .monsters import AIState

    px, py = dungeon.party_x, dungeon.party_y
    dist_to_player = manhattan_distance(mx, my, px, py)

    # Dead monsters don't move
    if monster.hp <= 0:
        return None

    # CHASE: if player is within chase range, move toward them
    if dist_to_player <= monster.chase_range:
        monster.ai_state = AIState.CHASE
        # If already adjacent, signal an attack by returning the player's tile.
        # The caller (_monster_turns) routes a move onto the player into combat.
        if dist_to_player == 1:
            return (px, py)
        # Otherwise move closer
        new_pos = simple_chase(dungeon, mx, my, px, py)
        return new_pos if new_pos else None

    # GUARD: if too far from spawn, return toward spawn
    if monster.ai_state == AIState.GUARD:
        dist_from_spawn = manhattan_distance(mx, my, monster.spawn_x, monster.spawn_y)
        if dist_from_spawn > monster.guard_range:
            new_pos = simple_chase(dungeon, mx, my, monster.spawn_x, monster.spawn_y)
            return new_pos if new_pos else None

    # WANDER: random movement
    neighbors = get_neighbors(mx, my)
    random.shuffle(neighbors)
    # 50% chance to just stay put (don't wander every turn)
    if random.random() < 0.5:
        return None
    for nx, ny in neighbors:
        if is_walkable(dungeon, nx, ny):
            return (nx, ny)

    return None  # can't move
