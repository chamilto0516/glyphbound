from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .fov import TORCH_RADIUS, SCROLL_RADIUS


class ItemKind(Enum):
    WEAPON   = "Weapon"
    ARMOR    = "Armor"
    POTION   = "Potion"
    TREASURE = "Treasure"
    SCROLL   = "Scroll"


class EquipSlot(Enum):
    WEAPON    = "weapon"
    ARMOR     = "armor"
    HELMET    = "helmet"
    SHIELD    = "shield"
    RING      = "ring"       # items use this; equip() auto-routes to ring_left/ring_right
    RING_LEFT  = "ring_left"
    RING_RIGHT = "ring_right"
    AMULET    = "amulet"
    BOOTS     = "boots"
    GLOVES    = "gloves"


@dataclass
class Item:
    name: str
    kind: ItemKind
    glyph: str          = "?"
    attack_bonus: int   = 0
    defense_bonus: int  = 0
    damage_reduction: int = 0  # armor/shields: flat damage subtracted from each hit taken
    hp_bonus: int       = 0   # potions: restored on use, accessories: permanent max HP
    mp_bonus: int       = 0   # potions: restored on use, accessories: permanent max MP
    gold_value: int     = 0
    equip_slot: EquipSlot | None = field(default=None)
    damage_sides: int   = 0   # 0 = static damage equal to damage_count
    damage_count: int   = 1   # number of dice, or static value when sides=0
    is_unique: bool     = False  # named/special items
    warrior_only: bool  = False  # requires Warrior class to equip
    two_handed: bool    = False  # weapons: occupies both hands; no off-hand / dual-wield
    backstab_bonus: float = 0.0  # weapons: added to a Thief's per-hit backstab chance
    thief_only: bool    = False  # requires Thief class to equip
    strikes: int        = 1      # weapons: number of attacks made per combat turn
    undead_bonus_sides: int = 0  # weapons: extra damage dice vs undead (0 = none)
    undead_bonus_count: int = 1  # weapons: number of undead-bonus dice
    invuln_turns: int   = 0     # scrolls: rounds of invulnerability granted
    light_radius: int   = 0     # >0: emits light when equipped (or, for scrolls, when read)
    xp_bonus: int       = 0     # potions: XP granted on use; treasures: XP granted on pickup
    heal_on_pickup: int = 0     # treasure: HP restored immediately when stepped on
    throwable: bool     = False  # weapons: usable as a ranged single-target attack via targeting mode
    thrown_range: int   = 0      # max Chebyshev range when thrown; 0 = default (5)
    thrown_consumed: bool = True  # True: item is lost/lands on the ground when thrown

    def __str__(self) -> str:
        parts = [self.name]
        if self.attack_bonus:
            parts.append(f"+{self.attack_bonus} ATK")
        if self.two_handed:
            parts.append("2H")
        if self.strikes > 1:
            parts.append(f"{self.strikes} strikes")
        if self.undead_bonus_sides:
            parts.append(f"+{self.undead_bonus_count}d{self.undead_bonus_sides} vs undead")
        if self.defense_bonus:
            parts.append(f"+{self.defense_bonus} DEF")
        if self.damage_reduction:
            parts.append(f"+{self.damage_reduction} DR")
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

# ── Class starting weapons ─────────────────────────────────────────────────────
ITEM_RUSTY_SWORD = Item(
    name="Rusty Sword", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=1, gold_value=4, equip_slot=EquipSlot.WEAPON,
    damage_sides=4, damage_count=1,   # 1d4 — Warrior starter
)
ITEM_ADEPT_STAFF = Item(
    name="Adept Staff", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=1, gold_value=4, equip_slot=EquipSlot.WEAPON,
    damage_sides=4, damage_count=1,   # 1d4 — Wizard starter
)
ITEM_SNEAKY_DAGGER = Item(
    name="Sneaky Dagger", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=1, gold_value=4, equip_slot=EquipSlot.WEAPON,
    damage_sides=4, damage_count=1,   # 1d4 — Thief starter
    backstab_bonus=0.10,              # sharpens the Thief's backstab
    throwable=True, thrown_range=5,
)
ITEM_ACOLYTE_MACE = Item(
    name="Acolyte Mace", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=1, gold_value=5, equip_slot=EquipSlot.WEAPON,
    damage_sides=6, damage_count=1,   # 1d6 — Cleric starter
)
ITEM_DAGGER = Item(
    name="Dagger", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=2, gold_value=5, equip_slot=EquipSlot.WEAPON,
    damage_sides=4, damage_count=1,   # 1d4
    throwable=True, thrown_range=5,
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
    warrior_only=True, two_handed=True,
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
    warrior_only=True, two_handed=True,
)
ITEM_MAUL = Item(
    name="Maul", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=4, gold_value=60, equip_slot=EquipSlot.WEAPON,
    damage_sides=6, damage_count=3,    # 3d6
    warrior_only=True, two_handed=True,
)

# ── Warrior-only Heavy Armor ───────────────────────────────────────────────────
ITEM_PLATE_MAIL = Item(
    name="Plate Mail", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=3, damage_reduction=2, gold_value=120, equip_slot=EquipSlot.ARMOR,
    warrior_only=True,
)
ITEM_GREAT_HELM = Item(
    name="Great Helm", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=2, damage_reduction=1, gold_value=70, equip_slot=EquipSlot.HELMET,
    warrior_only=True,
)
ITEM_KITE_SHIELD = Item(
    name="Kite Shield", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=1, damage_reduction=2, gold_value=80, equip_slot=EquipSlot.SHIELD,
    warrior_only=True,
)

# ── Named/Unique Weapons ───────────────────────────────────────────────────────
ITEM_FANG = Item(
    name="Fang", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=3, gold_value=120, equip_slot=EquipSlot.WEAPON,
    damage_sides=6, damage_count=1,   # 1d6, but strikes three times per turn
    strikes=3, backstab_bonus=0.10,   # a quick thief blade; each strike can backstab
    is_unique=True, thief_only=True,
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
    is_unique=True, warrior_only=True, two_handed=True,
)

ITEM_LEATHER_CAP = Item(
    name="Leather Cap", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=1, gold_value=4, equip_slot=EquipSlot.HELMET,
)
ITEM_LEATHER_ARMOR = Item(
    name="Leather Armor", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=1, damage_reduction=1, gold_value=10, equip_slot=EquipSlot.ARMOR,
)
ITEM_SMALL_SHIELD = Item(
    name="Small Shield", kind=ItemKind.ARMOR, glyph="]",
    damage_reduction=1, gold_value=8, equip_slot=EquipSlot.SHIELD,
)
ITEM_CHAIN_MAIL = Item(
    name="Chain Mail", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=2, damage_reduction=1, gold_value=30, equip_slot=EquipSlot.ARMOR,
)
ITEM_IRON_HELM = Item(
    name="Iron Helm", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=1, damage_reduction=1, gold_value=15, equip_slot=EquipSlot.HELMET,
)
ITEM_TOWER_SHIELD = Item(
    name="Tower Shield", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=1, damage_reduction=2, gold_value=25, equip_slot=EquipSlot.SHIELD,
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
ITEM_BOOTS_OF_SPEED = Item(
    name="Boots of Speed", kind=ItemKind.ARMOR, glyph="[",
    defense_bonus=0, gold_value=45, equip_slot=EquipSlot.BOOTS,
)
ITEM_LEATHER_BOOTS = Item(
    name="Leather Boots", kind=ItemKind.ARMOR, glyph="[",
    defense_bonus=1, gold_value=20, equip_slot=EquipSlot.BOOTS,
)
ITEM_IRON_BOOTS = Item(
    name="Iron Boots", kind=ItemKind.ARMOR, glyph="[",
    defense_bonus=1, damage_reduction=1, gold_value=40, equip_slot=EquipSlot.BOOTS,
)
ITEM_LEATHER_GLOVES = Item(
    name="Leather Gloves", kind=ItemKind.ARMOR, glyph="[",
    defense_bonus=0, attack_bonus=1, gold_value=18, equip_slot=EquipSlot.GLOVES,
)
ITEM_GAUNTLETS = Item(
    name="Gauntlets", kind=ItemKind.ARMOR, glyph="[",
    defense_bonus=1, attack_bonus=1, gold_value=50, equip_slot=EquipSlot.GLOVES,
    warrior_only=True,
)
ITEM_THIEF_GLOVES = Item(
    name="Thief's Gloves", kind=ItemKind.ARMOR, glyph="[",
    defense_bonus=0, attack_bonus=2, gold_value=60, equip_slot=EquipSlot.GLOVES,
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
ITEM_POTION_OF_KNOWLEDGE = Item(
    name="Potion of Knowledge", kind=ItemKind.POTION, glyph="!",
    xp_bonus=10, gold_value=35,
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
    name="Torch", kind=ItemKind.WEAPON, glyph="i",
    gold_value=10, equip_slot=EquipSlot.SHIELD,   # held in the off-hand
    damage_sides=0, damage_count=1,               # a feeble 1 damage if swung
    light_radius=TORCH_RADIUS,
)
ITEM_RUG = Item(
    name="Ornate Rug", kind=ItemKind.TREASURE, glyph="~",
    gold_value=15,
)
ITEM_ANCIENT_TOME = Item(
    name="Ancient Tome", kind=ItemKind.TREASURE, glyph="%",
    gold_value=40,
)
ITEM_IDOL = Item(
    name="Idol", kind=ItemKind.TREASURE, glyph="&",
    gold_value=60,
)
ITEM_SILVER_CANDLESTICK = Item(
    name="Silver Candlestick", kind=ItemKind.TREASURE, glyph="|",
    gold_value=20,
)
ITEM_INK_VIAL = Item(
    name="Ink Vial", kind=ItemKind.TREASURE, glyph="~",
    gold_value=35,
)
ITEM_CRACKED_RUNE_FRAGMENT = Item(
    name="Cracked Rune Fragment", kind=ItemKind.TREASURE, glyph="§",
    gold_value=0, xp_bonus=5,
)
ITEM_BLESSED_CHALICE = Item(
    name="Blessed Chalice", kind=ItemKind.TREASURE, glyph="Y",
    gold_value=15, heal_on_pickup=5,
)

# ── Scrolls ────────────────────────────────────────────────────────────────────
ITEM_SCROLL_FIREBALL = Item(
    name="Scroll of Fireball", kind=ItemKind.SCROLL, glyph="?",
    gold_value=40,
    damage_sides=6, damage_count=3,   # 3d6 fire damage
)
ITEM_SCROLL_HEAL = Item(
    name="Scroll of Heal", kind=ItemKind.SCROLL, glyph="?",
    gold_value=30,
    hp_bonus=20,                      # restore 20 HP
)
ITEM_SCROLL_INVULNERABILITY = Item(
    name="Scroll of Invulnerability", kind=ItemKind.SCROLL, glyph="?",
    gold_value=60,
    invuln_turns=3,                   # immune to attacks for 3 rounds
)
ITEM_SCROLL_ILLUMINATION = Item(
    name="Scroll of Illumination", kind=ItemKind.SCROLL, glyph="?",
    gold_value=45,
    light_radius=SCROLL_RADIUS,       # lights the floor; no hand needed
)

# ── Magic light items (light without giving up a hand) ──────────────────────────
ITEM_SUNBLADE = Item(
    name="Sunblade", kind=ItemKind.WEAPON, glyph="/",
    attack_bonus=4, gold_value=180, equip_slot=EquipSlot.WEAPON,
    damage_sides=8, damage_count=1,   # 1d8
    undead_bonus_sides=8, undead_bonus_count=1,  # +1d8 radiant damage vs undead
    light_radius=8,
)
ITEM_AEGIS_OF_DAWN = Item(
    name="Aegis of Dawn", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=2, damage_reduction=1, gold_value=160, equip_slot=EquipSlot.SHIELD,
    is_unique=True, light_radius=8,
)
ITEM_STARLIT_HELM = Item(
    name="Starlit Helm", kind=ItemKind.ARMOR, glyph="]",
    defense_bonus=1, damage_reduction=1, gold_value=150, equip_slot=EquipSlot.HELMET,
    is_unique=True, light_radius=10,
)

# ── Loot Pools ─────────────────────────────────────────────────────────────────

COMMON_WEAPONS = [ITEM_DAGGER, ITEM_SHORT_SWORD, ITEM_STAFF, ITEM_MACE]
RARE_WEAPONS = [ITEM_BROAD_SWORD, ITEM_LONG_SWORD, ITEM_BATTLE_AXE, ITEM_SUNBLADE]
UNIQUE_WEAPONS = [ITEM_FANG, ITEM_FLAMEBRAND]

HEAVY_WEAPONS = [ITEM_GREAT_SWORD, ITEM_WAR_HAMMER, ITEM_HALBERD, ITEM_MAUL]
HEAVY_ARMOR   = [ITEM_PLATE_MAIL, ITEM_GREAT_HELM, ITEM_KITE_SHIELD]
UNIQUE_HEAVY_WEAPONS = [ITEM_GORECLEAVER]

COMMON_ARMOR = [ITEM_LEATHER_CAP, ITEM_LEATHER_ARMOR, ITEM_SMALL_SHIELD]
RARE_ARMOR = [ITEM_CHAIN_MAIL, ITEM_IRON_HELM, ITEM_TOWER_SHIELD]

ACCESSORIES = [
    ITEM_RING_OF_PROTECTION, ITEM_AMULET_OF_VITALITY, ITEM_RING_OF_CLARITY,
    ITEM_LEATHER_BOOTS, ITEM_LEATHER_GLOVES,
]
RARE_ACCESSORIES = [
    ITEM_BOOTS_OF_SPEED, ITEM_IRON_BOOTS, ITEM_GAUNTLETS, ITEM_THIEF_GLOVES,
]

POTIONS = [ITEM_HEALTH_POTION, ITEM_MANA_POTION, ITEM_POTION_OF_KNOWLEDGE]
ELIXIRS = [ITEM_ELIXIR_VITALITY, ITEM_ELIXIR_CLARITY]

TREASURE = [
    ITEM_GEM, ITEM_RUG,
    ITEM_ANCIENT_TOME, ITEM_IDOL, ITEM_SILVER_CANDLESTICK, ITEM_INK_VIAL,
    ITEM_CRACKED_RUNE_FRAGMENT, ITEM_BLESSED_CHALICE,
]
GOLD = [ITEM_GOLD_PILE_SMALL, ITEM_GOLD_PILE_MEDIUM, ITEM_GOLD_PILE_LARGE]

SCROLLS = [ITEM_SCROLL_FIREBALL, ITEM_SCROLL_HEAL, ITEM_SCROLL_INVULNERABILITY, ITEM_SCROLL_ILLUMINATION]


def shop_stock(floor: int) -> list:
    """Return the shop's curated inventory for the given floor depth."""
    # A torch and a scroll of illumination are always for sale — light is a staple.
    stock = [ITEM_HEALTH_POTION, ITEM_MANA_POTION, ITEM_TORCH, ITEM_SCROLL_ILLUMINATION]
    # Basic weapons available from the very first floor so no class is stuck
    # flailing with a starter weapon against early monsters.
    stock += [ITEM_DAGGER, ITEM_STAFF, ITEM_MACE, ITEM_SHORT_SWORD]
    if floor >= 2:
        stock += [ITEM_ELIXIR_VITALITY, ITEM_ELIXIR_CLARITY]
    if floor >= 3:
        stock += [ITEM_BROAD_SWORD]
    if floor >= 4:
        stock += [ITEM_LEATHER_ARMOR, ITEM_SMALL_SHIELD, ITEM_IRON_HELM, ITEM_LEATHER_BOOTS, ITEM_LEATHER_GLOVES]
    if floor >= 5:
        stock += [ITEM_LONG_SWORD, ITEM_RING_OF_PROTECTION]
    if floor >= 6:
        stock += [ITEM_CHAIN_MAIL, ITEM_SCROLL_HEAL, ITEM_SCROLL_INVULNERABILITY, ITEM_IRON_BOOTS, ITEM_GAUNTLETS]
    if floor >= 7:
        stock += [ITEM_BATTLE_AXE, ITEM_SCROLL_FIREBALL, ITEM_BOOTS_OF_SPEED, ITEM_THIEF_GLOVES]
    return stock
