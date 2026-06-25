from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from .themes import Theme
    from .items import Item
    from .monsters import Monster

logger = logging.getLogger(__name__)

MAP_WIDTH  = 200
MAP_HEIGHT = 200

VOID        = 0
FLOOR       = 1
WALL        = 2
DOOR_CLOSED = 3
DOOR_OPEN   = 4
STAIR_DOWN  = 5
STAIR_UP    = 6


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
    floor: int = 1
    stair_down_pos: Optional[Tuple[int, int]] = None
    stair_up_pos: Optional[Tuple[int, int]] = None
    items: Dict[Tuple[int, int], List["Item"]] = field(default_factory=dict)
    monsters: Dict[Tuple[int, int], "Monster"] = field(default_factory=dict)

    def tile_at(self, x: int, y: int) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return VOID

    def place_item(self, x: int, y: int, item: "Item") -> None:
        self.items.setdefault((x, y), []).append(item)

    def items_at(self, x: int, y: int) -> List["Item"]:
        return self.items.get((x, y), [])

    def remove_item(self, x: int, y: int, item: "Item") -> None:
        stack = self.items.get((x, y), [])
        if item in stack:
            stack.remove(item)
            if not stack:
                del self.items[(x, y)]

    def drop_item(self, x: int, y: int, item: "Item") -> None:
        self.place_item(x, y, item)

    def place_monster(self, x: int, y: int, monster: "Monster") -> None:
        self.monsters[(x, y)] = monster

    def monster_at(self, x: int, y: int) -> "Monster | None":
        return self.monsters.get((x, y))

    def remove_monster(self, x: int, y: int) -> None:
        self.monsters.pop((x, y), None)

    def nearest_monster(self):
        """Return ((x, y), Monster) for the closest monster by Manhattan distance, or None."""
        return min(
            self.monsters.items(),
            key=lambda kv: abs(kv[0][0] - self.party_x) + abs(kv[0][1] - self.party_y),
            default=None,
        )

    def move_party(self, dx: int, dy: int) -> bool:
        """Move party, return True if they moved, False if blocked."""
        nx, ny = self.party_x + dx, self.party_y + dy
        if self.monster_at(nx, ny):
            return False  # caller handles combat, then calls this again or not
        tile = self.tile_at(nx, ny)
        if tile == DOOR_CLOSED:
            self.tiles[ny][nx] = DOOR_OPEN
            self.party_x, self.party_y = nx, ny
            return True
        elif tile in (FLOOR, DOOR_OPEN, STAIR_DOWN, STAIR_UP):
            self.party_x, self.party_y = nx, ny
            return True
        return False


def generate_dungeon(seed: int = None, theme: Theme = None, floor: int = 1, place_up_stair: bool = False) -> Dungeon:
    rng = random.Random(seed)

    if theme is None:
        from .themes import ALL_THEMES
        theme = rng.choice(ALL_THEMES)

    dungeon = Dungeon()
    dungeon.tiles = [[VOID] * MAP_WIDTH for _ in range(MAP_HEIGHT)]

    target = rng.randint(theme.min_rooms, theme.max_rooms)
    logger.info("Floor %d — theme=%s seed=%s target_rooms=%d", floor, theme.name, seed, target)
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
        logger.debug("room #%d (%d,%d) %dx%d center=%s",
                     len(rooms), room.x, room.y, room.w, room.h, room.center)

    logger.info("Phase 1: %d rooms placed in %d attempts", len(rooms), attempts)

    # Phase 2 — connect all rooms via minimum spanning tree
    _connect_rooms_mst(dungeon.tiles, rooms, rng, room_walls)

    # Phase 3 — add dead-end branch rooms
    dungeon.branch_rooms = _add_branch_rooms(dungeon.tiles, rooms, room_walls, rng, theme)
    logger.info("Phase 3: %d branch rooms", len(dungeon.branch_rooms))

    dungeon.rooms = rooms
    dungeon.party_x, dungeon.party_y = rooms[0].center
    dungeon.theme = theme
    dungeon.floor = floor

    # Place stairs — down in the room farthest from the start, up in the start room
    start_cx, start_cy = rooms[0].center
    farthest = max(
        rooms[1:],
        key=lambda r: abs(r.center[0] - start_cx) + abs(r.center[1] - start_cy),
        default=rooms[0],
    )
    dx, dy = farthest.center
    dungeon.tiles[dy][dx] = STAIR_DOWN
    dungeon.stair_down_pos = (dx, dy)

    if place_up_stair:
        ux, uy = start_cx, start_cy
        dungeon.tiles[uy][ux] = STAIR_UP
        dungeon.stair_up_pos = (ux, uy)
    logger.info("Stairs down at %s; up at %s", dungeon.stair_down_pos, dungeon.stair_up_pos)

    item_count = 0
    if floor == 1:
        from .items import ITEM_CLUB, ITEM_LEATHER_CAP
        dungeon.place_item(start_cx + 1, start_cy, ITEM_CLUB)
        dungeon.place_item(start_cx - 1, start_cy, ITEM_LEATHER_CAP)
        logger.info("item %s (%s) at %s", ITEM_CLUB.name, ITEM_CLUB.kind.value, (start_cx + 1, start_cy))
        logger.info("item %s (%s) at %s", ITEM_LEATHER_CAP.name, ITEM_LEATHER_CAP.kind.value, (start_cx - 1, start_cy))
        item_count += 2

    # Scatter one Elixir of Vitality and one Elixir of Clarity in random rooms.
    from .items import ITEM_ELIXIR_VITALITY, ITEM_ELIXIR_CLARITY
    elixir_rooms = rng.sample(rooms[1:], min(2, len(rooms) - 1))
    for room, elixir in zip(elixir_rooms, [ITEM_ELIXIR_VITALITY, ITEM_ELIXIR_CLARITY]):
        ex, ey = room.center
        dungeon.place_item(ex, ey, elixir)
        logger.info("item %s (%s) at %s", elixir.name, elixir.kind.value, (ex, ey))
        item_count += 1

    # Place random loot: potions, gold, weapons in remaining rooms
    item_count += _place_random_loot(dungeon, rooms, rng, floor)

    # Place one of each monster type in separate rooms, spread across the map.
    # Sort candidates by distance from start so goblin lands near start,
    # orc mid-range, troll deep — each picked from its own third of the list.
    from .monsters import ALL_SPAWNERS
    candidate_rooms = [
        r for r in rooms[1:]
        if r.center != (dx, dy)
    ]
    candidate_rooms.sort(
        key=lambda r: abs(r.center[0] - start_cx) + abs(r.center[1] - start_cy)
    )
    n = len(candidate_rooms)
    monster_count = 0
    if n >= len(ALL_SPAWNERS):
        third = max(1, n // len(ALL_SPAWNERS))
        for i, spawner in enumerate(ALL_SPAWNERS):
            zone_start = i * third
            zone_end   = zone_start + third if i < len(ALL_SPAWNERS) - 1 else n
            zone       = candidate_rooms[zone_start:zone_end]
            room       = rng.choice(zone)
            mx, my     = room.center
            m = spawner()
            dungeon.place_monster(mx, my, m)
            logger.info("monster %s '%s' hp%d atk%d def%d xp%d at %s",
                        m.name, m.glyph, m.hp, m.attack, m.defense, m.xp_value, (mx, my))
            monster_count += 1
    else:
        # fewer rooms than monster types — place what we can in distinct rooms
        rng.shuffle(candidate_rooms)
        for i, spawner in enumerate(ALL_SPAWNERS[:n]):
            mx, my = candidate_rooms[i].center
            m = spawner()
            dungeon.place_monster(mx, my, m)
            logger.info("monster %s '%s' hp%d atk%d def%d xp%d at %s",
                        m.name, m.glyph, m.hp, m.attack, m.defense, m.xp_value, (mx, my))
            monster_count += 1

    logger.info("Floor %d complete: %d rooms, %d branches, %d items, %d monsters",
                floor, len(rooms), len(dungeon.branch_rooms), item_count, monster_count)

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

    for dist, i, j in edges:
        if find(i) != find(j):
            parent[find(i)] = find(j)
            _carve_corridor(tiles, rooms[i], rooms[j], rng, room_walls)
            logger.debug("corridor room%d<->room%d dist=%d", i + 1, j + 1, dist)


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
        logger.debug("branch side=%s (%d,%d) %dx%d", side, branch.x, branch.y, branch.w, branch.h)

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


def _place_random_loot(dungeon: Dungeon, rooms: List[Room], rng: random.Random, floor: int) -> int:
    """Place random loot in rooms. Returns count of items placed."""
    from .items import (
        ITEM_HEALTH_POTION, ITEM_MANA_POTION, ITEM_GEM, ITEM_TORCH, ITEM_RUG,
        ITEM_DAGGER, ITEM_SHORT_SWORD, ITEM_STAFF, ITEM_LEATHER_ARMOR, ITEM_SMALL_SHIELD
    )

    # Loot pool based on floor difficulty
    potions = [ITEM_HEALTH_POTION, ITEM_MANA_POTION]
    treasure = [ITEM_GEM, ITEM_TORCH, ITEM_RUG]
    weapons = [ITEM_DAGGER, ITEM_SHORT_SWORD, ITEM_STAFF]
    armor = [ITEM_LEATHER_ARMOR, ITEM_SMALL_SHIELD]

    # Calculate number of loot drops: 2-4 per floor, increasing slightly with depth
    base_loot = 3
    floor_bonus = min(floor // 2, 3)  # +1 item every 2 floors, capped at +3
    loot_count = rng.randint(base_loot, base_loot + 1) + floor_bonus

    # Pick random rooms for loot (skip the first room where player starts)
    available_rooms = rooms[1:] if len(rooms) > 1 else rooms
    loot_rooms = rng.sample(available_rooms, min(loot_count, len(available_rooms)))

    placed = 0
    for room in loot_rooms:
        # Weighted random selection: potions most common, weapons/armor rarer
        roll = rng.random()
        if roll < 0.4:  # 40% potions
            item = rng.choice(potions)
        elif roll < 0.65:  # 25% treasure
            item = rng.choice(treasure)
        elif roll < 0.85:  # 20% weapons
            item = rng.choice(weapons)
        else:  # 15% armor
            item = rng.choice(armor)

        # Place slightly offset from center to avoid overlap with monsters/stairs
        cx, cy = room.center
        dx = rng.choice([-1, 0, 1])
        dy = rng.choice([-1, 0, 1])
        loot_x, loot_y = cx + dx, cy + dy

        dungeon.place_item(loot_x, loot_y, item)
        logger.info("loot %s (%s) at %s", item.name, item.kind.value, (loot_x, loot_y))
        placed += 1

    return placed


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
