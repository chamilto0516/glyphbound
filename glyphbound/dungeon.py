import random
from dataclasses import dataclass, field
from typing import List, Set, Tuple

MAP_WIDTH  = 500
MAP_HEIGHT = 500

VOID        = 0
FLOOR       = 1
WALL        = 2
DOOR_CLOSED = 3
DOOR_OPEN   = 4

TILE_GLYPHS: dict = {
    VOID:        " ",
    FLOOR:       ".",
    WALL:        "#",
    DOOR_CLOSED: "+",
    DOOR_OPEN:   "/",
}

PARTY_GLYPH = "@"

MIN_ROOMS  = 8
MAX_ROOMS  = 15
MIN_ROOM_W = 6
MAX_ROOM_W = 16
MIN_ROOM_H = 4
MAX_ROOM_H = 10


@dataclass
class Room:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> Tuple[int, int]:
        return self.x + self.w // 2, self.y + self.h // 2

    def overlaps(self, other: "Room", margin: int = 2) -> bool:
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
    party_x: int = 0
    party_y: int = 0

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


def generate_dungeon(seed: int = None) -> Dungeon:
    rng = random.Random(seed)
    dungeon = Dungeon()
    dungeon.tiles = [[VOID] * MAP_WIDTH for _ in range(MAP_HEIGHT)]

    target = rng.randint(MIN_ROOMS, MAX_ROOMS)
    rooms: List[Room] = []
    room_walls: Set[Tuple[int, int]] = set()
    attempts = 0

    while len(rooms) < target and attempts < 2000:
        attempts += 1
        w = rng.randint(MIN_ROOM_W, MAX_ROOM_W)
        h = rng.randint(MIN_ROOM_H, MAX_ROOM_H)
        x = rng.randint(2, MAP_WIDTH  - w - 3)
        y = rng.randint(2, MAP_HEIGHT - h - 3)
        room = Room(x, y, w, h)
        if any(room.overlaps(r) for r in rooms):
            continue
        _carve_room(dungeon.tiles, room, room_walls)
        if rooms:
            _carve_corridor(dungeon.tiles, rooms[-1], room, rng, room_walls)
        rooms.append(room)

    dungeon.rooms = rooms
    dungeon.party_x, dungeon.party_y = rooms[0].center
    return dungeon


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
