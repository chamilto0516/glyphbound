from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .items import Item, ITEM_CLUB, ITEM_SHORT_SWORD, ITEM_BROAD_SWORD


class MonsterKind(Enum):
    GOBLIN   = "Goblin"
    ORC      = "Orc"
    TROLL    = "Troll"
    SKELETON = "Skeleton"
    ZOMBIE   = "Zombie"


@dataclass
class Monster:
    kind: MonsterKind
    name: str
    glyph: str
    hp: int
    max_hp: int
    attack: int
    defense: int
    xp_value: int
    is_undead: bool = False
    weapon: Optional[Item] = field(default=None)


def spawn_goblin() -> Monster:
    return Monster(
        kind=MonsterKind.GOBLIN,
        name="Goblin",
        glyph="g",
        hp=5, max_hp=5,
        attack=1, defense=1,
        xp_value=1,
        weapon=ITEM_CLUB,
    )


def spawn_orc() -> Monster:
    return Monster(
        kind=MonsterKind.ORC,
        name="Orc",
        glyph="o",
        hp=12, max_hp=12,
        attack=3, defense=2,
        xp_value=3,
        weapon=ITEM_SHORT_SWORD,
    )


def spawn_troll() -> Monster:
    return Monster(
        kind=MonsterKind.TROLL,
        name="Troll",
        glyph="T",
        hp=20, max_hp=20,
        attack=5, defense=3,
        xp_value=6,
        weapon=ITEM_BROAD_SWORD,
    )


def spawn_skeleton() -> Monster:
    return Monster(
        kind=MonsterKind.SKELETON,
        name="Skeleton",
        glyph="s",
        hp=8, max_hp=8,
        attack=2, defense=1,
        xp_value=2,
        is_undead=True,
        weapon=ITEM_SHORT_SWORD,
    )


def spawn_zombie() -> Monster:
    return Monster(
        kind=MonsterKind.ZOMBIE,
        name="Zombie",
        glyph="z",
        hp=15, max_hp=15,
        attack=4, defense=2,
        xp_value=4,
        is_undead=True,
        weapon=ITEM_CLUB,
    )


# Ordered weakest→strongest; used by the dungeon placer.
ALL_SPAWNERS = [spawn_goblin, spawn_skeleton, spawn_orc, spawn_zombie, spawn_troll]
