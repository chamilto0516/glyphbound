from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from .items import (
    Item,
    ITEM_DAGGER, ITEM_SHORT_SWORD, ITEM_BROAD_SWORD,
    ITEM_MACE, ITEM_LONG_SWORD, ITEM_BATTLE_AXE,
    ITEM_GOLD_PILE_SMALL, ITEM_GOLD_PILE_MEDIUM, ITEM_GOLD_PILE_LARGE,
    ITEM_GEM,
    COMMON_WEAPONS, COMMON_ARMOR, RARE_WEAPONS, RARE_ARMOR,
    ACCESSORIES, POTIONS, ELIXIRS,
)
from .status_effects import EffectType, StatusEffect


class MonsterKind(Enum):
    # Floor 1+
    GOBLIN      = "Goblin"
    SKELETON    = "Skeleton"
    # Floor 2+
    ORC         = "Orc"
    ZOMBIE      = "Zombie"
    BUGBEAR     = "Bugbear"
    SPIDER      = "Spider"
    # Floor 3+
    TROLL       = "Troll"
    MUMMY       = "Mummy"
    WIGHT       = "Wight"
    # Floor 4+
    OWLBEAR     = "Owlbear"
    WRAITH      = "Wraith"
    # Floor 5+
    UMBER_HULK  = "Umber Hulk"
    VAMPIRE     = "Vampire"
    # Floor 7+
    DRAGON      = "Dragon"


class AIState(Enum):
    WANDER = "wander"    # random movement
    CHASE  = "chase"     # pursue player
    GUARD  = "guard"     # stay near spawn point


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
    min_floor: int       = 1
    is_undead: bool      = False
    weapon: Optional[Item] = field(default=None)

    # AI state
    ai_state: AIState = AIState.WANDER
    spawn_x: int = 0
    spawn_y: int = 0
    chase_range: int = 8
    guard_range: int = 5
    frozen_turns: int = 0   # >0: skips its AI turn (e.g. after the player flees)
    forced_drops: List[Item] = field(default_factory=list)  # guaranteed drops (e.g. floor-1 torch)

    # Status effects system
    status_effects: Dict[EffectType, StatusEffect] = field(default_factory=dict)
    on_hit_effect: Optional[EffectType] = None   # effect applied to player on successful hit
    on_hit_duration: int = 0                     # turns the effect lasts
    on_hit_potency: int = 0                      # effect strength (damage, etc.)
    on_hit_chance: float = 0.0                   # probability (0.0-1.0) to apply on hit

    def drop_loot(self) -> List[Item]:
        """Generate random loot on death."""
        loot: List[Item] = list(self.forced_drops)
        k = self.kind

        if k == MonsterKind.GOBLIN:
            loot.append(ITEM_GOLD_PILE_SMALL)
            if random.random() < 0.10:
                loot.append(random.choice(COMMON_WEAPONS))

        elif k == MonsterKind.SKELETON:
            loot.append(ITEM_GOLD_PILE_SMALL)
            if random.random() < 0.15:
                loot.append(random.choice(COMMON_WEAPONS + COMMON_ARMOR))

        elif k == MonsterKind.ORC:
            loot.append(ITEM_GOLD_PILE_MEDIUM)
            if random.random() < 0.20:
                loot.append(random.choice(COMMON_WEAPONS))
            if random.random() < 0.10:
                loot.append(random.choice(POTIONS))

        elif k == MonsterKind.ZOMBIE:
            loot.append(ITEM_GOLD_PILE_SMALL)
            if random.random() < 0.20:
                loot.append(random.choice(POTIONS))

        elif k == MonsterKind.BUGBEAR:
            loot.append(ITEM_GOLD_PILE_MEDIUM)
            if random.random() < 0.25:
                loot.append(random.choice(COMMON_WEAPONS + COMMON_ARMOR))
            if random.random() < 0.10:
                loot.append(random.choice(POTIONS))

        elif k == MonsterKind.SPIDER:
            loot.append(ITEM_GOLD_PILE_SMALL)
            if random.random() < 0.15:
                loot.append(random.choice(POTIONS))

        elif k == MonsterKind.TROLL:
            loot.append(ITEM_GOLD_PILE_LARGE)
            if random.random() < 0.30:
                loot.append(random.choice(COMMON_WEAPONS))
            if random.random() < 0.20:
                loot.append(random.choice(COMMON_ARMOR))

        elif k == MonsterKind.MUMMY:
            loot.append(ITEM_GOLD_PILE_MEDIUM)
            loot.append(ITEM_GEM)
            if random.random() < 0.20:
                loot.append(random.choice(POTIONS))

        elif k == MonsterKind.WIGHT:
            loot.append(ITEM_GOLD_PILE_MEDIUM)
            if random.random() < 0.25:
                loot.append(random.choice(COMMON_WEAPONS + RARE_ARMOR))

        elif k == MonsterKind.OWLBEAR:
            loot.append(ITEM_GOLD_PILE_LARGE)
            if random.random() < 0.30:
                loot.append(random.choice(RARE_WEAPONS))

        elif k == MonsterKind.WRAITH:
            # Wraiths carry cursed riches — gem + chance at accessory
            loot.append(ITEM_GEM)
            if random.random() < 0.25:
                loot.append(random.choice(ACCESSORIES))

        elif k == MonsterKind.UMBER_HULK:
            loot.append(ITEM_GOLD_PILE_LARGE)
            if random.random() < 0.35:
                loot.append(random.choice(RARE_WEAPONS + RARE_ARMOR))
            if random.random() < 0.15:
                loot.append(random.choice(POTIONS))

        elif k == MonsterKind.VAMPIRE:
            loot.append(ITEM_GEM)
            loot.append(ITEM_GOLD_PILE_LARGE)
            if random.random() < 0.40:
                loot.append(random.choice(ACCESSORIES))
            if random.random() < 0.25:
                loot.append(random.choice(RARE_WEAPONS))

        elif k == MonsterKind.DRAGON:
            # Dragon hoard: guaranteed large gold + gem + rare item
            loot.append(ITEM_GOLD_PILE_LARGE)
            loot.append(ITEM_GOLD_PILE_LARGE)
            loot.append(ITEM_GEM)
            loot.append(random.choice(RARE_WEAPONS + RARE_ARMOR))
            if random.random() < 0.50:
                loot.append(random.choice(ACCESSORIES))
            if random.random() < 0.30:
                loot.append(random.choice(ELIXIRS))

        return loot


# ── Floor 1+ ───────────────────────────────────────────────────────────────────

def spawn_goblin() -> Monster:
    return Monster(
        kind=MonsterKind.GOBLIN, name="Goblin", glyph="g",
        hp=5, max_hp=5, attack=1, defense=1, xp_value=1,
        min_floor=1, weapon=None,
        ai_state=AIState.WANDER, chase_range=10,
    )


def spawn_skeleton() -> Monster:
    return Monster(
        kind=MonsterKind.SKELETON, name="Skeleton", glyph="s",
        hp=8, max_hp=8, attack=2, defense=1, xp_value=2,
        min_floor=1, is_undead=True, weapon=ITEM_SHORT_SWORD,
        ai_state=AIState.WANDER, chase_range=7,
    )


# ── Floor 2+ ───────────────────────────────────────────────────────────────────

def spawn_orc() -> Monster:
    return Monster(
        kind=MonsterKind.ORC, name="Orc", glyph="o",
        hp=12, max_hp=12, attack=3, defense=2, xp_value=3,
        min_floor=2, weapon=ITEM_SHORT_SWORD,
        ai_state=AIState.WANDER, chase_range=8,
    )


def spawn_zombie() -> Monster:
    return Monster(
        kind=MonsterKind.ZOMBIE, name="Zombie", glyph="z",
        hp=15, max_hp=15, attack=4, defense=2, xp_value=4,
        min_floor=2, is_undead=True, weapon=None,
        ai_state=AIState.WANDER, chase_range=5,
    )


def spawn_bugbear() -> Monster:
    return Monster(
        kind=MonsterKind.BUGBEAR, name="Bugbear", glyph="b",
        hp=18, max_hp=18, attack=4, defense=2, xp_value=5,
        min_floor=2, weapon=ITEM_MACE,
        ai_state=AIState.WANDER, chase_range=9,
    )


def spawn_spider() -> Monster:
    return Monster(
        kind=MonsterKind.SPIDER, name="Spider", glyph="s",
        hp=10, max_hp=10, attack=3, defense=2, xp_value=3,
        min_floor=2, weapon=None,  # venomous bite
        ai_state=AIState.WANDER, chase_range=7,
        on_hit_effect=EffectType.POISONED, on_hit_duration=4, on_hit_potency=2, on_hit_chance=0.30,
    )


# ── Floor 3+ ───────────────────────────────────────────────────────────────────

def spawn_troll() -> Monster:
    return Monster(
        kind=MonsterKind.TROLL, name="Troll", glyph="T",
        hp=25, max_hp=25, attack=5, defense=3, xp_value=7,
        min_floor=3, weapon=ITEM_BROAD_SWORD,
        ai_state=AIState.GUARD, chase_range=6, guard_range=8,
    )


def spawn_mummy() -> Monster:
    return Monster(
        kind=MonsterKind.MUMMY, name="Mummy", glyph="M",
        hp=20, max_hp=20, attack=5, defense=4, xp_value=8,
        min_floor=3, is_undead=True, weapon=None,
        ai_state=AIState.WANDER, chase_range=6,
    )


def spawn_wight() -> Monster:
    return Monster(
        kind=MonsterKind.WIGHT, name="Wight", glyph="W",
        hp=18, max_hp=18, attack=6, defense=3, xp_value=9,
        min_floor=3, is_undead=True, weapon=ITEM_LONG_SWORD,
        ai_state=AIState.WANDER, chase_range=8,
    )


# ── Floor 4+ ───────────────────────────────────────────────────────────────────

def spawn_owlbear() -> Monster:
    return Monster(
        kind=MonsterKind.OWLBEAR, name="Owlbear", glyph="O",
        hp=30, max_hp=30, attack=7, defense=4, xp_value=12,
        min_floor=4, weapon=None,  # attacks with claws/beak
        ai_state=AIState.GUARD, chase_range=7, guard_range=6,
        on_hit_effect=EffectType.STUNNED, on_hit_duration=1, on_hit_potency=0, on_hit_chance=0.20,
    )


def spawn_wraith() -> Monster:
    return Monster(
        kind=MonsterKind.WRAITH, name="Wraith", glyph="\"",
        hp=22, max_hp=22, attack=7, defense=5, xp_value=14,
        min_floor=4, is_undead=True, weapon=None,
        ai_state=AIState.WANDER, chase_range=10,
        on_hit_effect=EffectType.SILENCED, on_hit_duration=3, on_hit_potency=0, on_hit_chance=0.15,
    )


# ── Floor 5+ ───────────────────────────────────────────────────────────────────

def spawn_umber_hulk() -> Monster:
    return Monster(
        kind=MonsterKind.UMBER_HULK, name="Umber Hulk", glyph="U",
        hp=40, max_hp=40, attack=8, defense=5, xp_value=18,
        min_floor=5, weapon=None,  # massive claws
        ai_state=AIState.GUARD, chase_range=7, guard_range=6,
        on_hit_effect=EffectType.STUNNED, on_hit_duration=1, on_hit_potency=0, on_hit_chance=0.25,
    )


def spawn_vampire() -> Monster:
    return Monster(
        kind=MonsterKind.VAMPIRE, name="Vampire", glyph="V",
        hp=35, max_hp=35, attack=9, defense=6, xp_value=22,
        min_floor=5, is_undead=True, weapon=None,
        ai_state=AIState.WANDER, chase_range=12,
    )


# ── Floor 7+ ───────────────────────────────────────────────────────────────────

def spawn_dragon() -> Monster:
    return Monster(
        kind=MonsterKind.DRAGON, name="Dragon", glyph="D",
        hp=60, max_hp=60, attack=12, defense=8, xp_value=50,
        min_floor=7, weapon=None,  # claws and fire breath flavour
        ai_state=AIState.GUARD, chase_range=10, guard_range=10,
        on_hit_effect=EffectType.BURNING, on_hit_duration=3, on_hit_potency=3, on_hit_chance=0.30,
    )


# ── Spawn table ────────────────────────────────────────────────────────────────
# Ordered weakest→strongest. Dungeon placer filters by min_floor.

ALL_SPAWNERS = [
    spawn_goblin,       # floor 1+
    spawn_skeleton,     # floor 1+
    spawn_orc,          # floor 2+
    spawn_zombie,       # floor 2+
    spawn_bugbear,      # floor 2+
    spawn_spider,       # floor 2+
    spawn_troll,        # floor 3+
    spawn_mummy,        # floor 3+
    spawn_wight,        # floor 3+
    spawn_owlbear,      # floor 4+
    spawn_wraith,       # floor 4+
    spawn_umber_hulk,   # floor 5+
    spawn_vampire,      # floor 5+
    spawn_dragon,       # floor 7+
]
