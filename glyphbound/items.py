from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ItemKind(Enum):
    WEAPON   = "Weapon"
    ARMOR    = "Armor"
    POTION   = "Potion"
    TREASURE = "Treasure"


class EquipSlot(Enum):
    WEAPON  = "weapon"
    ARMOR   = "armor"
    HELMET  = "helmet"
    SHIELD  = "shield"


@dataclass
class Item:
    name: str
    kind: ItemKind
    glyph: str          = "?"
    attack_bonus: int   = 0
    defense_bonus: int  = 0
    hp_bonus: int       = 0   # potions: restored on use
    mp_bonus: int       = 0   # potions: restored on use
    gold_value: int     = 0
    equip_slot: EquipSlot | None = field(default=None)
    damage_sides: int   = 0   # 0 = static damage equal to damage_count
    damage_count: int   = 1   # number of dice, or static value when sides=0

    def __str__(self) -> str:
        parts = [self.name]
        if self.attack_bonus:
            parts.append(f"+{self.attack_bonus} ATK")
        if self.defense_bonus:
            parts.append(f"+{self.defense_bonus} DEF")
        if self.hp_bonus:
            parts.append(f"+{self.hp_bonus} HP")
        if self.mp_bonus:
            parts.append(f"+{self.mp_bonus} MP")
        if self.gold_value and self.kind == ItemKind.TREASURE:
            parts.append(f"{self.gold_value}gp")
        return "  ".join(parts)


# ── Item catalog ───────────────────────────────────────────────────────────────

ITEM_CLUB = Item(
    name="Club", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=1, gold_value=2, equip_slot=EquipSlot.WEAPON,
    damage_sides=0, damage_count=1,   # static 1 damage
)
ITEM_DAGGER = Item(
    name="Dagger", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=2, gold_value=5, equip_slot=EquipSlot.WEAPON,
    damage_sides=4, damage_count=1,   # 1d4
)
ITEM_SHORT_SWORD = Item(
    name="Short Sword", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=3, gold_value=15, equip_slot=EquipSlot.WEAPON,
    damage_sides=6, damage_count=1,   # 1d6
)
ITEM_BROAD_SWORD = Item(
    name="Broad Sword", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=4, gold_value=30, equip_slot=EquipSlot.WEAPON,
    damage_sides=8, damage_count=1,   # 1d8
)
ITEM_STAFF = Item(
    name="Staff", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=2, gold_value=8, equip_slot=EquipSlot.WEAPON,
    damage_sides=4, damage_count=1,   # 1d4
)

ITEM_LEATHER_CAP = Item(
    name="Leather Cap", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=1, gold_value=4, equip_slot=EquipSlot.HELMET,
)
ITEM_LEATHER_ARMOR = Item(
    name="Leather Armor", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=2, gold_value=10, equip_slot=EquipSlot.ARMOR,
)
ITEM_SMALL_SHIELD = Item(
    name="Small Shield", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=1, gold_value=8, equip_slot=EquipSlot.SHIELD,
)

ITEM_HEALTH_POTION = Item(
    name="Health Potion", kind=ItemKind.POTION, glyph="!",
    hp_bonus=10, gold_value=20,
)
ITEM_MANA_POTION = Item(
    name="Mana Potion", kind=ItemKind.POTION, glyph="!",
    mp_bonus=10, gold_value=20,
)
# Full-restore potions (green / purple)
ITEM_ELIXIR_VITALITY = Item(
    name="Elixir of Vitality", kind=ItemKind.POTION, glyph="!",
    hp_bonus=999, gold_value=80,   # use_potion caps at max_hp
)
ITEM_ELIXIR_CLARITY = Item(
    name="Elixir of Clarity", kind=ItemKind.POTION, glyph="!",
    mp_bonus=999, gold_value=80,   # use_potion caps at max_mp
)

ITEM_GEM = Item(
    name="Gem", kind=ItemKind.TREASURE, glyph="*",
    gold_value=50,
)
ITEM_TORCH = Item(
    name="Torch", kind=ItemKind.TREASURE, glyph="i",
    gold_value=3,
)
ITEM_RUG = Item(
    name="Ornate Rug", kind=ItemKind.TREASURE, glyph="~",
    gold_value=15,
)
