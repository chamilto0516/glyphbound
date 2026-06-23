from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .items import EquipSlot, Item, ItemKind
from .spells import Spell, SpellEffect, WIZARD_SPELLS, CLERIC_SPELLS


class CharacterClass(Enum):
    WARRIOR = "Warrior"
    WIZARD  = "Wizard"
    THIEF   = "Thief"
    CLERIC  = "Cleric"


_CLASS_STATS = {
    CharacterClass.WARRIOR: {"hp": 20, "attack": 6, "defense": 4, "mp": 0},
    CharacterClass.WIZARD:  {"hp": 10, "attack": 2, "defense": 1, "mp": 20},
    CharacterClass.THIEF:   {"hp": 14, "attack": 4, "defense": 2, "mp": 0},
    CharacterClass.CLERIC:  {"hp": 16, "attack": 3, "defense": 3, "mp": 15},
}


@dataclass
class Player:
    name: str
    char_class: CharacterClass
    hp: int      = 0
    max_hp: int  = 0
    xp: int      = 0
    level: int   = 1
    mp: int      = 0
    max_mp: int  = 0
    gold: int    = 0

    # base stats from class; equipped gear adds on top via properties
    _base_attack: int  = field(default=0, repr=False)
    _base_defense: int = field(default=0, repr=False)

    inventory: List[Item]             = field(default_factory=list)
    equipped:  Dict[str, Item]        = field(default_factory=dict)  # slot name → Item
    spells:    List[Spell]            = field(default_factory=list)
    temp_defense_bonus: int           = 0   # cleared after each combat

    def __post_init__(self) -> None:
        stats = _CLASS_STATS[self.char_class]
        self.max_hp        = stats["hp"]
        self.hp            = stats["hp"]
        self._base_attack  = stats["attack"]
        self._base_defense = stats["defense"]
        self.max_mp        = stats["mp"]
        self.mp            = stats["mp"]
        if self.char_class == CharacterClass.WIZARD:
            self.spells = list(WIZARD_SPELLS)
        elif self.char_class == CharacterClass.CLERIC:
            self.spells = list(CLERIC_SPELLS)

    # ── Computed stats ─────────────────────────────────────────────────────────

    @property
    def attack(self) -> int:
        bonus = sum(i.attack_bonus for i in self.equipped.values())
        return self._base_attack + bonus

    @property
    def defense(self) -> int:
        bonus = sum(i.defense_bonus for i in self.equipped.values())
        return self._base_defense + bonus + self.temp_defense_bonus

    # ── Inventory actions ──────────────────────────────────────────────────────

    def pick_up(self, item: Item) -> str:
        self.inventory.append(item)
        return f"Picked up {item.name}."

    def equip(self, item: Item) -> Tuple[str, Optional[Item]]:
        """Equip an item from inventory. Returns (message, unequipped_item_or_None)."""
        if item not in self.inventory:
            return "You don't have that.", None
        if item.equip_slot is None:
            return f"{item.name} cannot be equipped.", None
        slot = item.equip_slot.value
        displaced = self.equipped.get(slot)
        if displaced:
            self.inventory.append(displaced)
        self.equipped[slot] = item
        self.inventory.remove(item)
        msg = f"Equipped {item.name}."
        if displaced:
            msg += f" ({displaced.name} returned to inventory.)"
        return msg, displaced

    def unequip(self, slot: EquipSlot) -> str:
        item = self.equipped.pop(slot.value, None)
        if item is None:
            return "Nothing equipped there."
        self.inventory.append(item)
        return f"Unequipped {item.name}."

    def drop(self, item: Item) -> Tuple[str, bool]:
        """Remove from inventory or equipped. Returns (message, was_found)."""
        if item in self.inventory:
            self.inventory.remove(item)
            return f"Dropped {item.name}.", True
        for slot, eq in list(self.equipped.items()):
            if eq is item:
                del self.equipped[slot]
                return f"Dropped {item.name}.", True
        return f"You don't have {item.name}.", False

    def use_potion(self, item: Item) -> str:
        if item.kind != ItemKind.POTION:
            return f"{item.name} is not a potion."
        if item not in self.inventory:
            return "You don't have that."
        self.inventory.remove(item)
        msgs = []
        if item.hp_bonus:
            healed = min(item.hp_bonus, self.max_hp - self.hp)
            self.hp += healed
            msgs.append(f"+{healed} HP")
        if item.mp_bonus:
            restored = min(item.mp_bonus, self.max_mp - self.mp)
            self.mp += restored
            msgs.append(f"+{restored} MP")
        return f"Drank {item.name}. " + ("  ".join(msgs) if msgs else "No effect.")

    # ── Spells ─────────────────────────────────────────────────────────────────

    def cast_spell(self, spell: Spell) -> Tuple[str, int]:
        """
        Attempt to cast a spell. Returns (message, damage_dealt).
        damage_dealt is >0 only for DAMAGE spells — caller applies it to monster.
        DEF buff is applied in-place here.
        """
        if spell not in self.spells:
            return "You don't know that spell.", 0
        if self.mp < spell.mp_cost:
            return f"Not enough MP to cast {spell.name}. (need {spell.mp_cost})", 0
        self.mp -= spell.mp_cost
        if spell.effect == SpellEffect.DAMAGE:
            dmg = sum(random.randint(1, spell.damage_sides) for _ in range(spell.damage_count))
            return f"You cast {spell.name} for {dmg} damage!", dmg
        if spell.effect == SpellEffect.BUFF_DEF:
            bonus = sum(random.randint(1, spell.def_sides) for _ in range(spell.def_count))
            self.temp_defense_bonus += bonus
            return f"Magic Armor conjured! +{bonus} DEF for next combat.", 0
        if spell.effect == SpellEffect.HEAL:
            healed = sum(random.randint(1, spell.heal_sides) for _ in range(spell.heal_count))
            healed = min(healed, self.max_hp - self.hp)
            self.hp += healed
            return f"You cast {spell.name}. +{healed} HP restored. (HP: {self.hp}/{self.max_hp})", 0
        if spell.effect == SpellEffect.TURN_UNDEAD:
            return f"You invoke {spell.name}!", 0
        return f"Cast {spell.name}.", 0

    # ── Per-move tick ──────────────────────────────────────────────────────────

    def on_move(self) -> None:
        if self.mp < self.max_mp:
            self.mp = min(self.max_mp, self.mp + 1)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @property
    def has_mp(self) -> bool:
        return self.max_mp > 0

    def equipped_in(self, slot: EquipSlot) -> Optional[Item]:
        return self.equipped.get(slot.value)
