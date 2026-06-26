from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ItemKind(Enum):
    WEAPON   = "Weapon"
    ARMOR    = "Armor"
    POTION   = "Potion"
    TREASURE = "Treasure"
    SCROLL   = "Scroll"


class EquipSlot(Enum):
    WEAPON  = "weapon"
    ARMOR   = "armor"
    HELMET  = "helmet"
    SHIELD  = "shield"
    RING    = "ring"
    AMULET  = "amulet"


@dataclass
class Item:
    name: str
    kind: ItemKind
    glyph: str          = "?"
    attack_bonus: int   = 0
    defense_bonus: int  = 0
    hp_bonus: int       = 0   # potions: restored on use, accessories: permanent max HP
    mp_bonus: int       = 0   # potions: restored on use, accessories: permanent max MP
    gold_value: int     = 0
    equip_slot: EquipSlot | None = field(default=None)
    damage_sides: int   = 0   # 0 = static damage equal to damage_count
    damage_count: int   = 1   # number of dice, or static value when sides=0
    is_unique: bool     = False  # named/special items
    warrior_only: bool  = False  # requires Warrior class to equip

    def __str__(self) -> str:
        parts = [self.name]
        if self.attack_bonus:
            parts.append(f"+{self.attack_bonus} ATK")
        if self.defense_bonus:
            parts.append(f"+{self.defense_bonus} DEF")
        if self.hp_bonus and self.kind == ItemKind.POTION:
            parts.append(f"+{self.hp_bonus} HP")
        elif self.hp_bonus:
            parts.append(f"+{self.hp_bonus} max HP")
        if self.mp_bonus and self.kind == ItemKind.POTION:
            parts.append(f"+{self.mp_bonus} MP")
        elif self.mp_bonus:
            parts.append(f"+{self.mp_bonus} max MP")
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
ITEM_MACE = Item(
    name="Mace", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=2, gold_value=12, equip_slot=EquipSlot.WEAPON,
    damage_sides=6, damage_count=1,   # 1d6
)
ITEM_LONG_SWORD = Item(
    name="Long Sword", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=4, gold_value=40, equip_slot=EquipSlot.WEAPON,
    damage_sides=10, damage_count=1,   # 1d10
)
ITEM_BATTLE_AXE = Item(
    name="Battle Axe", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=5, gold_value=60, equip_slot=EquipSlot.WEAPON,
    damage_sides=6, damage_count=2,   # 2d6
)

# ── Warrior-only Heavy Weapons ────────────────────────────────────────────────
ITEM_GREAT_SWORD = Item(
    name="Great Sword", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=6, gold_value=80, equip_slot=EquipSlot.WEAPON,
    damage_sides=12, damage_count=1,   # 1d12
    warrior_only=True,
)
ITEM_WAR_HAMMER = Item(
    name="War Hammer", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=5, gold_value=70, equip_slot=EquipSlot.WEAPON,
    damage_sides=8, damage_count=2,    # 2d8
    warrior_only=True,
)
ITEM_HALBERD = Item(
    name="Halberd", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=7, gold_value=100, equip_slot=EquipSlot.WEAPON,
    damage_sides=10, damage_count=2,   # 2d10
    warrior_only=True,
)
ITEM_MAUL = Item(
    name="Maul", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=4, gold_value=60, equip_slot=EquipSlot.WEAPON,
    damage_sides=6, damage_count=3,    # 3d6
    warrior_only=True,
)

# ── Warrior-only Heavy Armor ───────────────────────────────────────────────────
ITEM_PLATE_MAIL = Item(
    name="Plate Mail", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=6, gold_value=120, equip_slot=EquipSlot.ARMOR,
    warrior_only=True,
)
ITEM_GREAT_HELM = Item(
    name="Great Helm", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=4, gold_value=70, equip_slot=EquipSlot.HELMET,
    warrior_only=True,
)
ITEM_KITE_SHIELD = Item(
    name="Kite Shield", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=4, gold_value=80, equip_slot=EquipSlot.SHIELD,
    warrior_only=True,
)

# ── Named/Unique Weapons ───────────────────────────────────────────────────────
ITEM_FANG = Item(
    name="Fang", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=3, gold_value=80, equip_slot=EquipSlot.WEAPON,
    damage_sides=6, damage_count=1,   # 1d6
    is_unique=True,
)
ITEM_FLAMEBRAND = Item(
    name="Flamebrand", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=5, gold_value=150, equip_slot=EquipSlot.WEAPON,
    damage_sides=10, damage_count=1,   # 1d10 + fire flavor
    is_unique=True,
)
ITEM_GORECLEAVER = Item(
    name="Gorecleaver", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=8, gold_value=250, equip_slot=EquipSlot.WEAPON,
    damage_sides=12, damage_count=2,   # 2d12
    is_unique=True, warrior_only=True,
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
ITEM_CHAIN_MAIL = Item(
    name="Chain Mail", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=3, gold_value=30, equip_slot=EquipSlot.ARMOR,
)
ITEM_IRON_HELM = Item(
    name="Iron Helm", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=2, gold_value=15, equip_slot=EquipSlot.HELMET,
)
ITEM_TOWER_SHIELD = Item(
    name="Tower Shield", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=3, gold_value=25, equip_slot=EquipSlot.SHIELD,
)

# ── Accessories ────────────────────────────────────────────────────────────────
ITEM_RING_OF_PROTECTION = Item(
    name="Ring of Protection", kind=ItemKind.ARMOR, glyph="=",
    defense_bonus=1, gold_value=50, equip_slot=EquipSlot.RING,
)
ITEM_AMULET_OF_VITALITY = Item(
    name="Amulet of Vitality", kind=ItemKind.ARMOR, glyph="\"",
    hp_bonus=5, gold_value=60, equip_slot=EquipSlot.AMULET,
)
ITEM_RING_OF_CLARITY = Item(
    name="Ring of Clarity", kind=ItemKind.ARMOR, glyph="=",
    mp_bonus=5, gold_value=60, equip_slot=EquipSlot.RING,
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

ITEM_GOLD_PILE_SMALL = Item(
    name="Gold Coins", kind=ItemKind.TREASURE, glyph="$",
    gold_value=5,
)
ITEM_GOLD_PILE_MEDIUM = Item(
    name="Gold Pile", kind=ItemKind.TREASURE, glyph="$",
    gold_value=15,
)
ITEM_GOLD_PILE_LARGE = Item(
    name="Large Gold Pile", kind=ItemKind.TREASURE, glyph="$",
    gold_value=30,
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

# ── Scrolls ────────────────────────────────────────────────────────────────────
# Note: Scroll effects not yet implemented; these are placeholders
ITEM_SCROLL_FIREBALL = Item(
    name="Scroll of Fireball", kind=ItemKind.SCROLL, glyph="?",
    gold_value=40,
)
ITEM_SCROLL_HEAL = Item(
    name="Scroll of Heal", kind=ItemKind.SCROLL, glyph="?",
    gold_value=30,
)
ITEM_SCROLL_TELEPORT = Item(
    name="Scroll of Teleport", kind=ItemKind.SCROLL, glyph="?",
    gold_value=50,
)

# ── Loot Pools ─────────────────────────────────────────────────────────────────

COMMON_WEAPONS = [ITEM_CLUB, ITEM_DAGGER, ITEM_SHORT_SWORD, ITEM_STAFF, ITEM_MACE]
RARE_WEAPONS = [ITEM_BROAD_SWORD, ITEM_LONG_SWORD, ITEM_BATTLE_AXE]
UNIQUE_WEAPONS = [ITEM_FANG, ITEM_FLAMEBRAND]

HEAVY_WEAPONS = [ITEM_GREAT_SWORD, ITEM_WAR_HAMMER, ITEM_HALBERD, ITEM_MAUL]
HEAVY_ARMOR   = [ITEM_PLATE_MAIL, ITEM_GREAT_HELM, ITEM_KITE_SHIELD]
UNIQUE_HEAVY_WEAPONS = [ITEM_GORECLEAVER]

COMMON_ARMOR = [ITEM_LEATHER_CAP, ITEM_LEATHER_ARMOR, ITEM_SMALL_SHIELD]
RARE_ARMOR = [ITEM_CHAIN_MAIL, ITEM_IRON_HELM, ITEM_TOWER_SHIELD]

ACCESSORIES = [ITEM_RING_OF_PROTECTION, ITEM_AMULET_OF_VITALITY, ITEM_RING_OF_CLARITY]

POTIONS = [ITEM_HEALTH_POTION, ITEM_MANA_POTION]
ELIXIRS = [ITEM_ELIXIR_VITALITY, ITEM_ELIXIR_CLARITY]

TREASURE = [ITEM_GEM, ITEM_TORCH, ITEM_RUG]
GOLD = [ITEM_GOLD_PILE_SMALL, ITEM_GOLD_PILE_MEDIUM, ITEM_GOLD_PILE_LARGE]

SCROLLS = [ITEM_SCROLL_FIREBALL, ITEM_SCROLL_HEAL, ITEM_SCROLL_TELEPORT]
