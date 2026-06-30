"""Field of view via recursive symmetric shadowcasting.

Light is blocked by walls and closed doors. The blocking tile itself is
visible (you see the wall face), but nothing beyond it. Open doors, floor,
stairs, and the shop are transparent.

All light sources (base vision, torches, scrolls, spells) differ only in
radius, so a single `compute_fov` call at the effective radius covers them
all.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Set, Tuple

if TYPE_CHECKING:
    from .dungeon import Dungeon

from .dungeon import WALL, DOOR_CLOSED

# Light radii (Manhattan-ish Euclidean tiles). Tuned to keep the dungeon dark.
BASE_VISION   = 5
TORCH_RADIUS  = 12
SCROLL_RADIUS = 18
SPELL_RADIUS  = 15

# Eight (xx, xy, yx, yy) transforms — one per octant.
_OCTANTS = [
    (1, 0, 0, 1), (0, 1, 1, 0),
    (0, -1, 1, 0), (-1, 0, 0, 1),
    (-1, 0, 0, -1), (0, -1, -1, 0),
    (0, 1, -1, 0), (1, 0, 0, -1),
]


def _blocks_sight(dungeon: "Dungeon", x: int, y: int) -> bool:
    return dungeon.tile_at(x, y) in (WALL, DOOR_CLOSED)


def compute_fov(dungeon: "Dungeon", ox: int, oy: int, radius: int) -> Set[Tuple[int, int]]:
    """Return the set of tiles visible from (ox, oy) within `radius`."""
    visible: Set[Tuple[int, int]] = {(ox, oy)}
    r2 = radius * radius
    for xx, xy, yx, yy in _OCTANTS:
        _cast_light(dungeon, ox, oy, 1, 1.0, 0.0, radius, r2, xx, xy, yx, yy, visible)
    return visible


def _cast_light(dungeon, ox, oy, row, start_slope, end_slope, radius, r2,
                xx, xy, yx, yy, visible) -> None:
    if start_slope < end_slope:
        return
    for j in range(row, radius + 1):
        dx, dy = -j - 1, -j
        blocked = False
        new_start = start_slope
        while dx <= 0:
            dx += 1
            # Translate octant-local (dx, dy) into map coordinates.
            mx = ox + dx * xx + dy * xy
            my = oy + dx * yx + dy * yy
            l_slope = (dx - 0.5) / (dy + 0.5)
            r_slope = (dx + 0.5) / (dy - 0.5)
            if start_slope < r_slope:
                continue
            if end_slope > l_slope:
                break

            if dx * dx + dy * dy <= r2:
                visible.add((mx, my))

            wall = _blocks_sight(dungeon, mx, my)
            if blocked:
                if wall:
                    new_start = r_slope
                    continue
                else:
                    blocked = False
                    start_slope = new_start
            else:
                if wall and j < radius:
                    blocked = True
                    _cast_light(dungeon, ox, oy, j + 1, start_slope, l_slope,
                                radius, r2, xx, xy, yx, yy, visible)
                    new_start = r_slope
        if blocked:
            break
