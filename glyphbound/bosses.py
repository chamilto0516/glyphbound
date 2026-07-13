"""Milestone boss definitions (floors 3, 5, 10).

Each theme has a Lesser (Floor 3 mini-boss) and Greater (Floor 5 real boss)
design. Floor 10's "major" boss reuses the Greater design scaled up via
scale_boss(). Boss kinds are intentionally excluded from ALL_SPAWNERS in
monsters.py — they are only ever placed explicitly by dungeon.py.
"""
from __future__ import annotations

from typing import Callable, Dict, Tuple

from .items import (
    ITEM_GOLD_PILE_LARGE, ITEM_GEM, ITEM_CRACKED_RUNE_FRAGMENT,
    ITEM_FLAMEBRAND, ITEM_AEGIS_OF_DAWN,
    ITEM_QUILL_OF_UNBINDING, ITEM_DUNGEONHEART_AMULET,
    ITEM_WARDENS_MANACLE, ITEM_BONECHOIR_CENSER, ITEM_SIGIL_CARVED_DAGGER,
    ITEM_ELIXIR_VITALITY,
)
from .monsters import Monster, MonsterKind, AIState, spawn_skeleton, spawn_spider, spawn_zombie
from .status_effects import EffectType

BOSS_FLOORS: Tuple[int, ...] = (3, 5, 10)


# ── Library ──────────────────────────────────────────────────────────────────

def boss_ink_wraith() -> Monster:
    return Monster(
        kind=MonsterKind.INK_WRAITH_LESSER, name="Ink Wraith", glyph="W",
        hp=45, max_hp=45, attack=8, defense=4, xp_value=30,
        min_floor=3, is_undead=True, weapon=None,
        ai_state=AIState.GUARD, chase_range=12, guard_range=12,
        on_hit_effect=EffectType.SILENCED, on_hit_duration=3, on_hit_potency=0, on_hit_chance=0.30,
        is_boss=True, boss_title="the Bound Marginalia",
        aoe_range=3, aoe_sides=4, aoe_count=2, aoe_effect=EffectType.SILENCED, aoe_cooldown_max=4,
        forced_drops=[ITEM_QUILL_OF_UNBINDING, ITEM_CRACKED_RUNE_FRAGMENT, ITEM_GOLD_PILE_LARGE],
    )


def boss_unbound_index() -> Monster:
    return Monster(
        kind=MonsterKind.UNBOUND_INDEX_GREATER, name="The Unbound Index", glyph="I",
        hp=90, max_hp=90, attack=12, defense=6, xp_value=70,
        min_floor=5, is_undead=True, weapon=None,
        ai_state=AIState.GUARD, chase_range=14, guard_range=14,
        on_hit_effect=EffectType.SILENCED, on_hit_duration=3, on_hit_potency=0, on_hit_chance=0.30,
        is_boss=True, boss_title="the Sentence That Reads Itself",
        phase_threshold=0.5,
        summon_spawner=spawn_skeleton, summon_count=2, summon_max=6, summon_cooldown_max=5,
        aoe_range=3, aoe_sides=5, aoe_count=2, aoe_effect=EffectType.SILENCED, aoe_cooldown_max=4,
        forced_drops=[ITEM_QUILL_OF_UNBINDING, ITEM_CRACKED_RUNE_FRAGMENT,
                       ITEM_GOLD_PILE_LARGE, ITEM_GEM],
    )


# ── Living Dungeon ───────────────────────────────────────────────────────────

def boss_gnashing_maw() -> Monster:
    return Monster(
        kind=MonsterKind.GNASHING_MAW_LESSER, name="Gnashing Maw", glyph="M",
        hp=50, max_hp=50, attack=9, defense=3, xp_value=32,
        min_floor=3, weapon=None,
        ai_state=AIState.GUARD, chase_range=12, guard_range=12,
        on_hit_effect=EffectType.POISONED, on_hit_duration=3, on_hit_potency=2, on_hit_chance=0.30,
        is_boss=True, boss_title="the Hungering Wall",
        aoe_range=2, aoe_sides=6, aoe_count=2, aoe_cooldown_max=4,
        forced_drops=[ITEM_DUNGEONHEART_AMULET, ITEM_CRACKED_RUNE_FRAGMENT, ITEM_GOLD_PILE_LARGE],
    )


def boss_heart_of_dungeon() -> Monster:
    return Monster(
        kind=MonsterKind.HEART_OF_DUNGEON_GREATER, name="Heart of the Dungeon", glyph="H",
        hp=100, max_hp=100, attack=13, defense=5, xp_value=75,
        min_floor=5, weapon=None,
        ai_state=AIState.GUARD, chase_range=14, guard_range=14,
        on_hit_effect=EffectType.POISONED, on_hit_duration=4, on_hit_potency=2, on_hit_chance=0.30,
        is_boss=True, boss_title="the Wall That Dreams",
        phase_threshold=0.5,
        summon_spawner=spawn_zombie, summon_count=2, summon_max=6, summon_cooldown_max=5,
        aoe_range=2, aoe_sides=6, aoe_count=3, aoe_cooldown_max=4,
        forced_drops=[ITEM_DUNGEONHEART_AMULET, ITEM_CRACKED_RUNE_FRAGMENT,
                       ITEM_GOLD_PILE_LARGE, ITEM_GEM],
    )


# ── Prison ───────────────────────────────────────────────────────────────────

def boss_wardens_shade() -> Monster:
    return Monster(
        kind=MonsterKind.WARDENS_SHADE_LESSER, name="Warden's Shade", glyph="S",
        hp=48, max_hp=48, attack=9, defense=4, xp_value=31,
        min_floor=3, is_undead=True, weapon=None,
        ai_state=AIState.GUARD, chase_range=12, guard_range=12,
        on_hit_effect=EffectType.BOUND, on_hit_duration=2, on_hit_potency=0, on_hit_chance=0.25,
        is_boss=True, boss_title="the Last Jailer",
        aoe_range=2, aoe_sides=5, aoe_count=2, aoe_effect=EffectType.BOUND, aoe_cooldown_max=4,
        forced_drops=[ITEM_WARDENS_MANACLE, ITEM_CRACKED_RUNE_FRAGMENT, ITEM_GOLD_PILE_LARGE],
    )


def boss_broken_chain_colossus() -> Monster:
    return Monster(
        kind=MonsterKind.BROKEN_CHAIN_GREATER, name="Broken-Chain Colossus", glyph="C",
        hp=95, max_hp=95, attack=13, defense=6, xp_value=72,
        min_floor=5, is_undead=True, weapon=None,
        ai_state=AIState.GUARD, chase_range=14, guard_range=14,
        on_hit_effect=EffectType.BOUND, on_hit_duration=2, on_hit_potency=0, on_hit_chance=0.25,
        is_boss=True, boss_title="the Warden Unmade",
        phase_threshold=0.5,
        summon_spawner=spawn_skeleton, summon_count=2, summon_max=6, summon_cooldown_max=5,
        aoe_range=2, aoe_sides=6, aoe_count=2, aoe_effect=EffectType.BOUND, aoe_cooldown_max=4,
        forced_drops=[ITEM_WARDENS_MANACLE, ITEM_CRACKED_RUNE_FRAGMENT,
                       ITEM_GOLD_PILE_LARGE, ITEM_GEM],
    )


# ── Catacombs ────────────────────────────────────────────────────────────────

def boss_bone_choir() -> Monster:
    return Monster(
        kind=MonsterKind.BONE_CHOIR_LESSER, name="Bone Choir", glyph="B",
        hp=46, max_hp=46, attack=8, defense=4, xp_value=30,
        min_floor=3, is_undead=True, weapon=None,
        ai_state=AIState.GUARD, chase_range=12, guard_range=12,
        is_boss=True, boss_title="the Rattling Verse",
        summon_spawner=spawn_skeleton, summon_count=2, summon_max=4, summon_cooldown_max=5,
        forced_drops=[ITEM_BONECHOIR_CENSER, ITEM_CRACKED_RUNE_FRAGMENT, ITEM_GOLD_PILE_LARGE],
    )


def boss_lich_cantor() -> Monster:
    return Monster(
        kind=MonsterKind.LICH_CANTOR_GREATER, name="The Lich Cantor", glyph="L",
        hp=88, max_hp=88, attack=12, defense=6, xp_value=70,
        min_floor=5, is_undead=True, weapon=None,
        ai_state=AIState.GUARD, chase_range=14, guard_range=14,
        on_hit_effect=EffectType.POISONED, on_hit_duration=3, on_hit_potency=2, on_hit_chance=0.25,
        is_boss=True, boss_title="the Final Hymn",
        phase_threshold=0.5,
        summon_spawner=spawn_skeleton, summon_count=2, summon_max=6, summon_cooldown_max=5,
        aoe_range=3, aoe_sides=6, aoe_count=2, aoe_effect=EffectType.POISONED, aoe_cooldown_max=4,
        forced_drops=[ITEM_BONECHOIR_CENSER, ITEM_CRACKED_RUNE_FRAGMENT,
                       ITEM_GOLD_PILE_LARGE, ITEM_GEM],
    )


# ── Ritual Sanctum ───────────────────────────────────────────────────────────

def boss_sigil_acolyte() -> Monster:
    return Monster(
        kind=MonsterKind.SIGIL_ACOLYTE_LESSER, name="Acolyte of the Sigil", glyph="A",
        hp=44, max_hp=44, attack=9, defense=3, xp_value=30,
        min_floor=3, weapon=None,
        ai_state=AIState.GUARD, chase_range=12, guard_range=12,
        on_hit_effect=EffectType.BURNING, on_hit_duration=3, on_hit_potency=2, on_hit_chance=0.30,
        is_boss=True, boss_title="the Kindled Devout",
        aoe_range=3, aoe_sides=5, aoe_count=2, aoe_effect=EffectType.BURNING, aoe_cooldown_max=4,
        forced_drops=[ITEM_SIGIL_CARVED_DAGGER, ITEM_CRACKED_RUNE_FRAGMENT, ITEM_GOLD_PILE_LARGE],
    )


def boss_sigil_incarnate() -> Monster:
    return Monster(
        kind=MonsterKind.SIGIL_INCARNATE_GREATER, name="The Sigil Incarnate", glyph="G",
        hp=92, max_hp=92, attack=13, defense=6, xp_value=74,
        min_floor=5, weapon=None,
        ai_state=AIState.GUARD, chase_range=14, guard_range=14,
        on_hit_effect=EffectType.BURNING, on_hit_duration=3, on_hit_potency=3, on_hit_chance=0.30,
        is_boss=True, boss_title="the Sign Made Flesh",
        phase_threshold=0.5,
        summon_spawner=spawn_zombie, summon_count=2, summon_max=6, summon_cooldown_max=5,
        aoe_range=3, aoe_sides=6, aoe_count=3, aoe_effect=EffectType.BURNING, aoe_cooldown_max=4,
        forced_drops=[ITEM_SIGIL_CARVED_DAGGER, ITEM_FLAMEBRAND, ITEM_CRACKED_RUNE_FRAGMENT,
                       ITEM_GOLD_PILE_LARGE],
    )


# ── Natural Caverns ──────────────────────────────────────────────────────────

def boss_broodmother() -> Monster:
    return Monster(
        kind=MonsterKind.BROODMOTHER_LESSER, name="Broodmother", glyph="P",
        hp=47, max_hp=47, attack=8, defense=4, xp_value=31,
        min_floor=3, weapon=None,
        ai_state=AIState.GUARD, chase_range=12, guard_range=12,
        on_hit_effect=EffectType.POISONED, on_hit_duration=4, on_hit_potency=2, on_hit_chance=0.35,
        is_boss=True, boss_title="the Broodwatcher",
        summon_spawner=spawn_spider, summon_count=2, summon_max=4, summon_cooldown_max=5,
        forced_drops=[ITEM_AEGIS_OF_DAWN, ITEM_CRACKED_RUNE_FRAGMENT, ITEM_GOLD_PILE_LARGE],
    )


def boss_stone_tyrant() -> Monster:
    return Monster(
        kind=MonsterKind.STONE_TYRANT_GREATER, name="The Stone Tyrant", glyph="T",
        hp=98, max_hp=98, attack=14, defense=7, xp_value=76,
        min_floor=5, weapon=None,
        ai_state=AIState.GUARD, chase_range=14, guard_range=14,
        on_hit_effect=EffectType.POISONED, on_hit_duration=4, on_hit_potency=3, on_hit_chance=0.30,
        is_boss=True, boss_title="the Cavern's Judgment",
        phase_threshold=0.5,
        summon_spawner=spawn_spider, summon_count=2, summon_max=6, summon_cooldown_max=5,
        aoe_range=2, aoe_sides=6, aoe_count=3, aoe_cooldown_max=4,
        forced_drops=[ITEM_AEGIS_OF_DAWN, ITEM_CRACKED_RUNE_FRAGMENT,
                       ITEM_GOLD_PILE_LARGE, ITEM_GEM],
    )


# ── Registry ─────────────────────────────────────────────────────────────────

BossPair = Tuple[Callable[[], Monster], Callable[[], Monster]]

BOSS_REGISTRY: Dict[str, BossPair] = {
    "Library":          (boss_ink_wraith, boss_unbound_index),
    "Living Dungeon":    (boss_gnashing_maw, boss_heart_of_dungeon),
    "Prison":            (boss_wardens_shade, boss_broken_chain_colossus),
    "Catacombs":         (boss_bone_choir, boss_lich_cantor),
    "Ritual Sanctum":    (boss_sigil_acolyte, boss_sigil_incarnate),
    "Natural Caverns":   (boss_broodmother, boss_stone_tyrant),
}
_DEFAULT_BOSS_PAIR: BossPair = (boss_ink_wraith, boss_unbound_index)


def scale_boss(m: Monster, floor: int) -> Monster:
    """Scale a Greater boss into its Floor-10 'major' form. Mutates in place."""
    m.max_hp = int(m.max_hp * 2)
    m.hp = m.max_hp
    m.attack = int(m.attack * 1.5)
    m.xp_value = m.xp_value * 2
    m.min_floor = floor
    if m.phase_threshold:
        m.phase_threshold = 0.6  # phases in earlier — harsher fight
    if m.summon_cooldown_max:
        m.summon_cooldown_max = max(2, m.summon_cooldown_max - 1)
        m.summon_max += 2
    if m.aoe_cooldown_max:
        m.aoe_cooldown_max = max(2, m.aoe_cooldown_max - 1)
    return m


def pick_boss(theme_name: str, floor: int) -> Monster:
    """Return the milestone boss for this theme + floor. floor should be in BOSS_FLOORS."""
    lesser, greater = BOSS_REGISTRY.get(theme_name, _DEFAULT_BOSS_PAIR)
    if floor == 3:
        return lesser()
    if floor == 5:
        return greater()
    return scale_boss(greater(), floor)
