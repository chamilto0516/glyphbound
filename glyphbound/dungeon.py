from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from .themes import Theme
    from .items import Item
    from .monsters import Monster
    from .traps import Trap

logger = logging.getLogger(__name__)

MAP_WIDTH  = 100
MAP_HEIGHT = 60

VOID        = 0
FLOOR       = 1
WALL        = 2
DOOR_CLOSED = 3
DOOR_OPEN   = 4
STAIR_DOWN  = 5
STAIR_UP    = 6
SHOP        = 7


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
    shop_pos: Optional[Tuple[int, int]] = None
    items: Dict[Tuple[int, int], List["Item"]] = field(default_factory=dict)
    monsters: Dict[Tuple[int, int], "Monster"] = field(default_factory=dict)
    traps: Dict[Tuple[int, int], "Trap"] = field(default_factory=dict)
    boss: Optional["Monster"] = None  # the milestone boss on this floor, if any

    # ── Lighting / field of view (per floor) ─────────────────────────────────
    ambient_light_radius: int = 0   # set by Scroll/Spell of Illumination; 0 = none
    explored: Set[Tuple[int, int]] = field(default_factory=set)   # ever seen this floor
    visible: Set[Tuple[int, int]]  = field(default_factory=set)   # lit right now

    def recompute_visibility(self, light_radius: int, reveal_all: bool = False) -> None:
        """Recompute the visible set from the party's position.

        `light_radius` is the player's own light reach (base vision plus any
        equipped light source). It's combined with the floor's ambient light
        (a scroll or spell of Illumination). When `reveal_all` is set (the
        --light debug flag) the whole map is treated as visible.
        """
        if reveal_all:
            self.visible = {
                (x, y) for y in range(self.height) for x in range(self.width)
            }
            self.explored |= self.visible
            return
        from .fov import compute_fov
        radius = max(light_radius, self.ambient_light_radius)
        self.visible = compute_fov(self, self.party_x, self.party_y, radius)
        self.explored |= self.visible

    def tile_at(self, x: int, y: int) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return VOID

    def place_item(self, x: int, y: int, item: "Item") -> None:
        self.items.setdefault((x, y), []).append(item)

    def can_hold_item(self, x: int, y: int) -> bool:
        """True if (x, y) is a plain walkable floor tile — never stairs/shop/doors.

        Items must never land on stairs (you'd descend instead of picking them
        up) or on the shop. Open floor only.
        """
        return self.tile_at(x, y) == FLOOR

    def find_item_tile(self, cx: int, cy: int, radius: int = 3) -> Optional[Tuple[int, int]]:
        """Find an open floor tile near (cx, cy) suitable for an item.

        Searches outward in rings from the center. Skips stairs, the shop,
        doors, walls, and tiles already holding an item. Returns None if no
        spot is found within `radius`.
        """
        for r in range(radius + 1):
            for oy in range(-r, r + 1):
                for ox in range(-r, r + 1):
                    if max(abs(ox), abs(oy)) != r:
                        continue  # only the current ring's perimeter
                    tx, ty = cx + ox, cy + oy
                    if self.can_hold_item(tx, ty) and (tx, ty) not in self.items:
                        return (tx, ty)
        return None

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

    def find_spawn_tile(self, cx: int, cy: int, radius: int = 4) -> Optional[Tuple[int, int]]:
        """Find an open floor tile near (cx, cy) for a monster.

        Skips stairs, shop, doors, walls, tiles holding another monster, and
        the player's start. Searches outward in rings. Returns None if no spot
        is found within `radius`.
        """
        for r in range(radius + 1):
            for oy in range(-r, r + 1):
                for ox in range(-r, r + 1):
                    if max(abs(ox), abs(oy)) != r:
                        continue  # only this ring's perimeter
                    tx, ty = cx + ox, cy + oy
                    if (self.tile_at(tx, ty) == FLOOR
                            and (tx, ty) not in self.monsters
                            and (tx, ty) != (self.party_x, self.party_y)):
                        return (tx, ty)
        return None

    def monster_at(self, x: int, y: int) -> "Monster | None":
        return self.monsters.get((x, y))

    def remove_monster(self, x: int, y: int) -> None:
        self.monsters.pop((x, y), None)

    def place_trap(self, x: int, y: int, trap: "Trap") -> None:
        self.traps[(x, y)] = trap

    def trap_at(self, x: int, y: int) -> "Trap | None":
        return self.traps.get((x, y))

    def remove_trap(self, x: int, y: int) -> None:
        self.traps.pop((x, y), None)

    def move_monster(self, old_x: int, old_y: int, new_x: int, new_y: int) -> bool:
        """Move a monster from (old_x, old_y) to (new_x, new_y). Returns True if moved."""
        monster = self.monsters.get((old_x, old_y))
        if not monster:
            return False
        # Check destination is not occupied by another monster
        if self.monster_at(new_x, new_y) is not None:
            return False
        # Check destination is walkable (not player — that triggers combat)
        tile = self.tile_at(new_x, new_y)
        if tile not in (FLOOR, DOOR_OPEN, STAIR_DOWN, STAIR_UP):
            return False
        # Move
        del self.monsters[(old_x, old_y)]
        self.monsters[(new_x, new_y)] = monster
        return True

    def nearest_monster(self):
        """Return ((x, y), Monster) for the closest monster by Manhattan distance, or None."""
        return min(
            self.monsters.items(),
            key=lambda kv: abs(kv[0][0] - self.party_x) + abs(kv[0][1] - self.party_y),
            default=None,
        )

    def monsters_in_radius(self, cx: int, cy: int, radius: int) -> List[Tuple[Tuple[int, int], "Monster"]]:
        """(pos, monster) pairs within Chebyshev `radius` of (cx, cy) — used for AOE resolution."""
        return [
            (pos, m) for pos, m in self.monsters.items()
            if max(abs(pos[0] - cx), abs(pos[1] - cy)) <= radius
        ]

    def visible_monsters(self, px: int, py: int, max_range: int = 0) -> List[Tuple[Tuple[int, int], "Monster"]]:
        """(pos, monster) pairs currently in self.visible, nearest-first, capped by max_range if >0.

        Used to seed the targeting cursor and drive Tab-cycling.
        """
        hits = []
        for pos, m in self.monsters.items():
            if pos not in self.visible:
                continue
            if max_range and max(abs(pos[0] - px), abs(pos[1] - py)) > max_range:
                continue
            hits.append((pos, m))
        hits.sort(key=lambda kv: abs(kv[0][0] - px) + abs(kv[0][1] - py))
        return hits

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
        elif tile in (FLOOR, DOOR_OPEN, STAIR_DOWN, STAIR_UP, SHOP):
            self.party_x, self.party_y = nx, ny
            return True
        return False


def generate_dungeon(seed: int = None, theme: "Theme | None" = None, floor: int = 1, place_up_stair: bool = False, theme_name: "str | None" = None) -> Dungeon:
    rng = random.Random(seed)

    if theme is None:
        from .themes import ALL_THEMES
        if theme_name is not None:
            matches = [t for t in ALL_THEMES if t.name.lower() == theme_name.lower()]
            theme = matches[0] if matches else rng.choice(ALL_THEMES)
        else:
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

    # Shop zone — 2×2 tiles in the largest eligible room (not start, not stair room)
    shop_candidates = [
        r for r in rooms[1:]
        if r.center != (dx, dy) and r.w >= 7 and r.h >= 7
    ]
    if shop_candidates:
        shop_room = max(shop_candidates, key=lambda r: r.w * r.h)
        sx, sy = shop_room.x + 2, shop_room.y + 2
        for oy in range(2):
            for ox in range(2):
                dungeon.tiles[sy + oy][sx + ox] = SHOP
        dungeon.shop_pos = (sx, sy)
        logger.info("Shop zone at %s in room %dx%d", dungeon.shop_pos, shop_room.w, shop_room.h)

    item_count = 0
    # Note: Starting gear (club, leather cap) now equipped on player by default

    # Scatter one Elixir of Vitality and one Elixir of Clarity in random rooms.
    from .items import ITEM_ELIXIR_VITALITY, ITEM_ELIXIR_CLARITY
    elixir_rooms = rng.sample(rooms[1:], min(2, len(rooms) - 1))
    for room, elixir in zip(elixir_rooms, [ITEM_ELIXIR_VITALITY, ITEM_ELIXIR_CLARITY]):
        cx, cy = room.center
        spot = dungeon.find_item_tile(cx, cy)
        if spot is None:
            continue  # no open tile (e.g. stair room) — skip rather than overlap
        dungeon.place_item(*spot, elixir)
        logger.info("item %s (%s) at %s", elixir.name, elixir.kind.value, spot)
        item_count += 1

    # Place random loot: potions, gold, weapons in remaining rooms
    item_count += _place_random_loot(dungeon, rooms, rng, floor)

    # Place monsters: filter eligible spawners by floor, scale count with depth.
    from .monsters import ALL_SPAWNERS
    eligible = [s for s in ALL_SPAWNERS if s().min_floor <= floor]

    # Monster count: 6 on floor 1, +2 every floor, capped at 24.
    target_monsters = min(6 + (floor - 1) * 2, 24)

    candidate_rooms = [
        r for r in rooms[1:]
        if r.center != (dx, dy)
    ]
    # Sort near→far so weaker monsters naturally land closer to start
    candidate_rooms.sort(
        key=lambda r: abs(r.center[0] - start_cx) + abs(r.center[1] - start_cy)
    )
    monster_count = 0
    # Round-robin across rooms so monsters spread out; multiple per room is fine.
    room_cursor = 0
    for _ in range(target_monsters):
        if not candidate_rooms:
            break
        # Pick a spawner weighted toward the stronger end as floors deepen
        if len(eligible) == 1:
            spawner = eligible[0]
        else:
            # Weight: monsters in the top half of the eligible list get more
            # weight on deeper floors.
            mid = len(eligible) // 2
            weights = [1] * mid + [1 + (floor // 2)] * (len(eligible) - mid)
            spawner = rng.choices(eligible, weights=weights, k=1)[0]

        # Cycle through rooms; find an open tile near the room's center.
        spot = None
        for _attempt in range(len(candidate_rooms)):
            room = candidate_rooms[room_cursor % len(candidate_rooms)]
            room_cursor += 1
            spot = dungeon.find_spawn_tile(*room.center)
            if spot is not None:
                break
        if spot is None:
            continue  # no open tile anywhere — give up on this monster

        mx, my = spot
        m = spawner()
        m.spawn_x, m.spawn_y = mx, my
        # The very first monster of floor 1 always carries a torch.
        if floor == 1 and monster_count == 0:
            from .items import ITEM_TORCH
            m.forced_drops.append(ITEM_TORCH)
        dungeon.place_monster(mx, my, m)
        logger.info("monster %s '%s' hp%d atk%d def%d xp%d at %s",
                    m.name, m.glyph, m.hp, m.attack, m.defense, m.xp_value, (mx, my))
        monster_count += 1

    # Place a milestone boss guarding the down-stair on floors 3/5/10.
    from .bosses import BOSS_FLOORS, pick_boss
    if floor in BOSS_FLOORS:
        boss_spot = dungeon.find_spawn_tile(dx, dy)
        if boss_spot is not None:
            bx, by = boss_spot
            boss = pick_boss(theme.name, floor)
            boss.spawn_x, boss.spawn_y = bx, by
            dungeon.place_monster(bx, by, boss)
            dungeon.boss = boss
            logger.info("boss %s '%s' hp%d atk%d def%d xp%d at %s guarding stairs at %s",
                        boss.name, boss.glyph, boss.hp, boss.attack, boss.defense,
                        boss.xp_value, (bx, by), (dx, dy))

    # Place traps: 2–5 traps per floor, scattered across non-start rooms
    from .traps import TRAP_MAKERS
    trap_count = rng.randint(2, 5)
    trap_candidates = rooms[1:] if len(rooms) > 1 else rooms
    trap_rooms = rng.sample(trap_candidates, min(trap_count, len(trap_candidates)))
    placed_traps = 0
    for room in trap_rooms:
        maker = rng.choice(TRAP_MAKERS)
        trap = maker()
        tx = rng.randint(room.x + 1, room.x + room.w - 2)
        ty = rng.randint(room.y + 1, room.y + room.h - 2)
        # Don't place on top of stairs or another trap
        if (tx, ty) != dungeon.stair_down_pos and (tx, ty) != dungeon.stair_up_pos \
                and not dungeon.trap_at(tx, ty):
            dungeon.place_trap(tx, ty, trap)
            placed_traps += 1
            logger.info("trap %s at %s", trap.name, (tx, ty))

    logger.info("Floor %d complete: %d rooms, %d branches, %d items, %d monsters, %d traps",
                floor, len(rooms), len(dungeon.branch_rooms), item_count, monster_count, placed_traps)

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
        bw = rng.randint(4, 6)
        bh = rng.randint(4, 5)

        if side == "top":
            if parent.w < 4:
                continue
            wx = rng.randint(parent.x + 1, parent.x + parent.w - 2)
            branch = Room(wx - bw // 2, parent.y - 1 - bh, bw, bh)
            conn = (wx, wx, branch.y + bh - 1, parent.y)
        elif side == "bottom":
            if parent.w < 4:
                continue
            wx = rng.randint(parent.x + 1, parent.x + parent.w - 2)
            branch = Room(wx - bw // 2, parent.y + parent.h + 1, bw, bh)
            conn = (wx, wx, parent.y + parent.h - 1, branch.y)
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
        COMMON_WEAPONS, RARE_WEAPONS, UNIQUE_WEAPONS,
        HEAVY_WEAPONS, HEAVY_ARMOR, UNIQUE_HEAVY_WEAPONS,
        COMMON_ARMOR, RARE_ARMOR, ACCESSORIES,
        POTIONS, TREASURE, SCROLLS
    )

    # Calculate number of loot drops: 3-6 per floor, increasing with depth
    base_loot = 3
    floor_bonus = min(floor // 2, 3)  # +1 item every 2 floors, capped at +3
    loot_count = rng.randint(base_loot, base_loot + 3) + floor_bonus

    # Pick random rooms for loot (skip the first room where player starts)
    available_rooms = rooms[1:] if len(rooms) > 1 else rooms
    loot_rooms = rng.sample(available_rooms, min(loot_count, len(available_rooms)))

    placed = 0
    for room in loot_rooms:
        # Weighted random selection with floor-based scaling
        roll = rng.random()

        # Common drops (60%)
        if roll < 0.35:  # 35% potions
            item = rng.choice(POTIONS)
        elif roll < 0.5:  # 15% treasure
            item = rng.choice(TREASURE)
        elif roll < 0.6:  # 10% scrolls
            item = rng.choice(SCROLLS)

        # Uncommon drops (30%)
        elif roll < 0.75:  # 15% common weapons
            item = rng.choice(COMMON_WEAPONS)
        elif roll < 0.9:  # 15% common armor
            item = rng.choice(COMMON_ARMOR)

        # Rare drops (8%)
        elif roll < 0.92 and floor >= 3:  # 3% rare weapons (floor 3+)
            item = rng.choice(RARE_WEAPONS)
        elif roll < 0.94 and floor >= 3:  # 2% rare armor (floor 3+)
            item = rng.choice(RARE_ARMOR)
        elif roll < 0.96 and floor >= 3:  # 2% heavy weapons (floor 3+)
            item = rng.choice(HEAVY_WEAPONS)
        elif roll < 0.98 and floor >= 4:  # 2% heavy armor (floor 4+)
            item = rng.choice(HEAVY_ARMOR)

        # Very rare drops (2%)
        elif roll < 0.99 and floor >= 5:  # 1% accessories (floor 5+)
            item = rng.choice(ACCESSORIES)
        else:  # 1% unique weapons (floor 7+)
            if floor >= 7:
                item = rng.choice(UNIQUE_WEAPONS + UNIQUE_HEAVY_WEAPONS)
            else:
                item = rng.choice(COMMON_WEAPONS)  # fallback

        # Find an open floor tile near the room center — never on stairs/shop.
        cx, cy = room.center
        spot = dungeon.find_item_tile(cx, cy)
        if spot is None:
            continue  # no eligible tile in this room — skip it
        dungeon.place_item(*spot, item)
        logger.info("loot %s (%s) at %s", item.name, item.kind.value, spot)
        placed += 1

    return placed


def _carve_h_tunnel(tiles: List[List[int]], x1: int, x2: int, y: int,
                    room_walls: Set[Tuple[int, int]]) -> None:
    door_placed = False
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if tiles[y][x] == WALL and (x, y) in room_walls:
            if not door_placed:
                tiles[y][x] = DOOR_CLOSED
                door_placed = True
            else:
                tiles[y][x] = FLOOR
        elif tiles[y][x] not in (FLOOR, DOOR_CLOSED, DOOR_OPEN):
            tiles[y][x] = FLOOR
        for ny in (y - 1, y + 1):
            if 0 <= ny < MAP_HEIGHT and tiles[ny][x] == VOID:
                tiles[ny][x] = WALL
    # Cap open endpoints
    for ex in (min(x1, x2) - 1, max(x1, x2) + 1):
        if 0 <= ex < MAP_WIDTH and tiles[y][ex] == VOID:
            tiles[y][ex] = WALL


def _carve_v_tunnel(tiles: List[List[int]], y1: int, y2: int, x: int,
                    room_walls: Set[Tuple[int, int]]) -> None:
    door_placed = False
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if tiles[y][x] == WALL and (x, y) in room_walls:
            if not door_placed:
                tiles[y][x] = DOOR_CLOSED
                door_placed = True
            else:
                tiles[y][x] = FLOOR
        elif tiles[y][x] not in (FLOOR, DOOR_CLOSED, DOOR_OPEN):
            tiles[y][x] = FLOOR
        for nx in (x - 1, x + 1):
            if 0 <= nx < MAP_WIDTH and tiles[y][nx] == VOID:
                tiles[y][nx] = WALL
    # Cap open endpoints
    for ey in (min(y1, y2) - 1, max(y1, y2) + 1):
        if 0 <= ey < MAP_HEIGHT and tiles[ey][x] == VOID:
            tiles[ey][x] = WALL


def dump_map_text(dungeon: "Dungeon") -> None:
    """Print the dungeon as ASCII to stdout; emit a connectivity summary to stderr."""
    import sys

    TILE_CHARS = {
        VOID:        ' ',
        FLOOR:       '.',
        WALL:        '#',
        DOOR_CLOSED: '+',
        DOOR_OPEN:   '-',
        STAIR_DOWN:  '>',
        STAIR_UP:    '<',
        SHOP:        '$',
    }
    LABELS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # Build char grid
    grid = [[TILE_CHARS.get(dungeon.tiles[y][x], '?') for x in range(dungeon.width)]
            for y in range(dungeon.height)]

    # Overlay room-center labels
    all_rooms = list(dungeon.rooms) + list(dungeon.branch_rooms)
    for idx, room in enumerate(all_rooms):
        cx, cy = room.center
        label = LABELS[idx] if idx < len(LABELS) else '.'
        grid[cy][cx] = label

    # Overlay party start
    grid[dungeon.party_y][dungeon.party_x] = '@'

    # Print map
    for row in grid:
        print(''.join(row))

    # Flood-fill from party start to find reachable tiles
    passable = {FLOOR, DOOR_CLOSED, DOOR_OPEN, STAIR_DOWN, STAIR_UP}
    visited: Set[Tuple[int, int]] = set()
    stack = [(dungeon.party_x, dungeon.party_y)]
    while stack:
        cx, cy = stack.pop()
        if (cx, cy) in visited:
            continue
        if not (0 <= cx < dungeon.width and 0 <= cy < dungeon.height):
            continue
        if dungeon.tiles[cy][cx] not in passable:
            continue
        visited.add((cx, cy))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (cx + dx, cy + dy)
            if nb not in visited:
                stack.append(nb)

    # Connectivity report
    reachable = 0
    disconnected = []
    for room in all_rooms:
        rx, ry = room.center
        if (rx, ry) in visited:
            reachable += 1
        else:
            disconnected.append((rx, ry))

    theme_name = dungeon.theme.name if dungeon.theme else "unknown"
    print(f"\n--- Map Summary ---", file=sys.stderr)
    print(f"Theme : {theme_name}", file=sys.stderr)
    print(f"Floor : {dungeon.floor}", file=sys.stderr)
    print(f"Rooms : {len(dungeon.rooms)} main + {len(dungeon.branch_rooms)} branch = {len(all_rooms)} total", file=sys.stderr)
    print(f"Reachable from @ : {reachable}/{len(all_rooms)}", file=sys.stderr)
    if disconnected:
        print(f"DISCONNECTED rooms ({len(disconnected)}):", file=sys.stderr)
        for pos in disconnected:
            print(f"  center at {pos}", file=sys.stderr)
    else:
        print("All rooms reachable.", file=sys.stderr)
