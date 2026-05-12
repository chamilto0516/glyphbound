from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from .themes import Theme

MAP_WIDTH  = 500
MAP_HEIGHT = 500

VOID        = 0
FLOOR       = 1
WALL        = 2
DOOR_CLOSED = 3
DOOR_OPEN   = 4


@dataclass
class Room:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> Tuple[int, int]:
        return self.x + self.w // 2, self.y + self.h // 2

    def overlaps(self, other: Room, margin: int = 2) -> bool:
        return (
            self.x - margin < other.x + other.w and
            self.x + self.w + margin > other.x and
            self.y - margin < other.y + other.h and
            self.y + self.h + margin > other.y
        )


@dataclass
class Dungeon:
    width: int = MAP_WIDTH
    height: int = MAP_HEIGHT
    tiles: List[List[int]] = field(default_factory=list)
    rooms: List[Room] = field(default_factory=list)
    branch_rooms: List[Room] = field(default_factory=list)
    party_x: int = 0
    party_y: int = 0
    theme: Optional[Theme] = field(default=None)

    def tile_at(self, x: int, y: int) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return VOID

    def move_party(self, dx: int, dy: int) -> None:
        nx, ny = self.party_x + dx, self.party_y + dy
        tile = self.tile_at(nx, ny)
        if tile == DOOR_CLOSED:
            self.tiles[ny][nx] = DOOR_OPEN
            self.party_x, self.party_y = nx, ny
        elif tile in (FLOOR, DOOR_OPEN):
            self.party_x, self.party_y = nx, ny


def generate_dungeon(seed: int = None, theme: Theme = None) -> Dungeon:
    rng = random.Random(seed)

    if theme is None:
        from .themes import ALL_THEMES
        theme = rng.choice(ALL_THEMES)

    dungeon = Dungeon()
    dungeon.tiles = [[VOID] * MAP_WIDTH for _ in range(MAP_HEIGHT)]

    target = rng.randint(theme.min_rooms, theme.max_rooms)
    rooms: List[Room] = []
    room_walls: Set[Tuple[int, int]] = set()
    attempts = 0

    # Phase 1 — place rooms
    while len(rooms) < target and attempts < 2000:
        attempts += 1
        w = rng.randint(theme.min_room_w, theme.max_room_w)
        h = rng.randint(theme.min_room_h, theme.max_room_h)
        x = rng.randint(2, MAP_WIDTH  - w - 3)
        y = rng.randint(2, MAP_HEIGHT - h - 3)
        room = Room(x, y, w, h)
        if any(room.overlaps(r, margin=1) for r in rooms):
            continue
        if rooms and not _room_within_corridor_range(room, rooms, theme.max_corridor):
            continue
        _carve_room(dungeon.tiles, room, room_walls)
        rooms.append(room)

    # Phase 2 — connect all rooms via minimum spanning tree
    _connect_rooms_mst(dungeon.tiles, rooms, rng, room_walls)

    # Phase 3 — add dead-end branch rooms
    dungeon.branch_rooms = _add_branch_rooms(dungeon.tiles, rooms, room_walls, rng, theme)

    dungeon.rooms = rooms
    dungeon.party_x, dungeon.party_y = rooms[0].center
    dungeon.theme = theme
    return dungeon


def _room_within_corridor_range(
    room: Room, existing: List[Room], max_dist: int
) -> bool:
    cx, cy = room.center
    return any(
        max(abs(cx - r.center[0]), abs(cy - r.center[1])) <= max_dist
        for r in existing
    )


def _connect_rooms_mst(
    tiles: List[List[int]],
    rooms: List[Room],
    rng: random.Random,
    room_walls: Set[Tuple[int, int]],
) -> None:
    N = len(rooms)
    if N < 2:
        return

    edges = sorted(
        (max(abs(rooms[i].center[0] - rooms[j].center[0]),
             abs(rooms[i].center[1] - rooms[j].center[1])), i, j)
        for i in range(N)
        for j in range(i + 1, N)
    )

    parent = list(range(N))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for _dist, i, j in edges:
        if find(i) != find(j):
            parent[find(i)] = find(j)
            _carve_corridor(tiles, rooms[i], rooms[j], rng, room_walls)


def _add_branch_rooms(
    tiles: List[List[int]],
    rooms: List[Room],
    room_walls: Set[Tuple[int, int]],
    rng: random.Random,
    theme: Theme,
) -> List[Room]:
    count = rng.randint(2, 4)
    branches: List[Room] = []
    all_rooms = list(rooms)
    attempts = 0

    while len(branches) < count and attempts < 40:
        attempts += 1
        parent = rng.choice(rooms)
        side = rng.choice(("top", "bottom", "left", "right"))
        bw = rng.randint(3, 5)
        bh = rng.randint(3, 4)

        if side == "top":
            if parent.w < 4:
                continue
            wx = rng.randint(parent.x + 1, parent.x + parent.w - 2)
            branch = Room(wx - bw // 2, parent.y - 1 - bh, bw, bh)
            conn = (wx, branch.y + bh - 1, wx, parent.y)
        elif side == "bottom":
            if parent.w < 4:
                continue
            wx = rng.randint(parent.x + 1, parent.x + parent.w - 2)
            branch = Room(wx - bw // 2, parent.y + parent.h + 1, bw, bh)
            conn = (wx, parent.y + parent.h - 1, wx, branch.y)
        elif side == "left":
            if parent.h < 4:
                continue
            wy = rng.randint(parent.y + 1, parent.y + parent.h - 2)
            branch = Room(parent.x - 1 - bw, wy - bh // 2, bw, bh)
            conn = (branch.x + bw - 1, parent.x, wy, wy)
        else:  # right
            if parent.h < 4:
                continue
            wy = rng.randint(parent.y + 1, parent.y + parent.h - 2)
            branch = Room(parent.x + parent.w + 1, wy - bh // 2, bw, bh)
            conn = (parent.x + parent.w - 1, branch.x, wy, wy)

        if (branch.x < 2 or branch.y < 2 or
                branch.x + branch.w > MAP_WIDTH  - 3 or
                branch.y + branch.h > MAP_HEIGHT - 3):
            continue
        if any(branch.overlaps(r, margin=1) for r in all_rooms):
            continue

        _carve_room(tiles, branch, room_walls)

        # conn encodes (x1, x2, y, y) for horizontal or (x, x, y1, y2) for vertical
        x1, x2, y1, y2 = conn
        if x1 == x2:
            _carve_v_tunnel(tiles, y1, y2, x1, room_walls)
        else:
            _carve_h_tunnel(tiles, x1, x2, y1, room_walls)

        all_rooms.append(branch)
        branches.append(branch)

    return branches


def _carve_room(tiles: List[List[int]], room: Room,
                room_walls: Set[Tuple[int, int]]) -> None:
    for y in range(room.y, room.y + room.h):
        for x in range(room.x, room.x + room.w):
            is_border = (y == room.y or y == room.y + room.h - 1 or
                         x == room.x or x == room.x + room.w - 1)
            if is_border:
                if tiles[y][x] == VOID:
                    tiles[y][x] = WALL
                    room_walls.add((x, y))
            else:
                tiles[y][x] = FLOOR


def _carve_corridor(tiles: List[List[int]], a: Room, b: Room,
                    rng: random.Random,
                    room_walls: Set[Tuple[int, int]]) -> None:
    ax, ay = a.center
    bx, by = b.center
    if rng.random() < 0.5:
        _carve_h_tunnel(tiles, ax, bx, ay, room_walls)
        _carve_v_tunnel(tiles, ay, by, bx, room_walls)
    else:
        _carve_v_tunnel(tiles, ay, by, ax, room_walls)
        _carve_h_tunnel(tiles, ax, bx, by, room_walls)


def _carve_h_tunnel(tiles: List[List[int]], x1: int, x2: int, y: int,
                    room_walls: Set[Tuple[int, int]]) -> None:
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if tiles[y][x] == WALL and (x, y) in room_walls:
            tiles[y][x] = DOOR_CLOSED
        elif tiles[y][x] not in (FLOOR, DOOR_CLOSED, DOOR_OPEN):
            tiles[y][x] = FLOOR
        for ny in (y - 1, y + 1):
            if 0 <= ny < MAP_HEIGHT and tiles[ny][x] == VOID:
                tiles[ny][x] = WALL


def _carve_v_tunnel(tiles: List[List[int]], y1: int, y2: int, x: int,
                    room_walls: Set[Tuple[int, int]]) -> None:
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if tiles[y][x] == WALL and (x, y) in room_walls:
            tiles[y][x] = DOOR_CLOSED
        elif tiles[y][x] not in (FLOOR, DOOR_CLOSED, DOOR_OPEN):
            tiles[y][x] = FLOOR
        for nx in (x - 1, x + 1):
            if 0 <= nx < MAP_WIDTH and tiles[y][nx] == VOID:
                tiles[y][nx] = WALL
