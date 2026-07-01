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

_LEVEL_UP_GAINS = {
    CharacterClass.WARRIOR: {"hp": 5, "attack": 1, "defense": 1, "mp": 0},
    CharacterClass.WIZARD:  {"hp": 3, "attack": 0, "defense": 0, "mp": 5},
    CharacterClass.THIEF:   {"hp": 4, "attack": 1, "defense": 1, "mp": 0},
    CharacterClass.CLERIC:  {"hp": 4, "attack": 0, "defense": 1, "mp": 3},
}

SLOT_LABELS: dict = {
    "weapon":     "main hand",
    "shield":     "off hand",
    "armor":      "body",
    "helmet":     "head",
    "ring_left":  "left ring",
    "ring_right": "right ring",
    "amulet":     "neck",
    "boots":      "boots",
    "gloves":     "gloves",
}

def slot_label(slot_value: str) -> str:
    return SLOT_LABELS.get(slot_value, slot_value)

# Keep private alias so internal equip() call doesn't break
_slot_label = slot_label


def xp_for_level(level: int) -> int:
    """Return cumulative XP needed to reach the given level."""
    if level <= 1:
        return 0
    if level == 2:
        return 10
    if level == 3:
        return 25
    total = 25
    multiplier = 2
    for lv in range(4, level + 1):
        total += 25 * multiplier
        multiplier *= 2
    return total


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

    # ── Run statistics ─────────────────────────────────────────────────────────
    stat_squares_traveled: int  = 0
    stat_floors_descended: int  = 0
    stat_items_found:      int  = 0
    stat_damage_taken:     int  = 0
    stat_mp_spent:         int  = 0
    stat_monsters_killed:  int  = 0
    stat_gold_collected:   int  = 0

    # base stats from class; equipped gear adds on top via properties
    _base_attack: int  = field(default=0, repr=False)
    _base_defense: int = field(default=0, repr=False)

    inventory: List[Item]             = field(default_factory=list)
    equipped:  Dict[str, Item]        = field(default_factory=dict)  # slot name → Item
    spells:    List[Spell]            = field(default_factory=list)
    temp_defense_bonus: int           = 0   # flat DEF from timed buffs; cleared when timer runs out
    temp_defense_turns: int           = 0   # turns remaining on temp_defense_bonus
    temp_attack_bonus: int            = 0   # cleared after each combat
    damage_absorb: int                = 0   # finite pool that soaks incoming damage (absorb spells)
    rage_turns_remaining: int         = 0   # counts down each attack while raging
    rage_used_this_floor: bool        = False  # once per floor
    invuln_turns_remaining: int       = 0   # rounds remaining of scroll invulnerability

    def __post_init__(self) -> None:
        stats = _CLASS_STATS[self.char_class]
        self.max_hp        = stats["hp"]
        self.hp            = stats["hp"]
        self._base_attack  = stats["attack"]
        self._base_defense = stats["defense"]
        self.max_mp        = stats["mp"]
        self.mp            = stats["mp"]
        self._learn_spells_for_level()
        self._equip_starting_gear()

    def _learn_spells_for_level(self) -> None:
        """Add all spells available at current level."""
        if self.char_class == CharacterClass.WIZARD:
            self.spells = [s for s in WIZARD_SPELLS if s.min_level <= self.level]
        elif self.char_class == CharacterClass.CLERIC:
            self.spells = [s for s in CLERIC_SPELLS if s.min_level <= self.level]

    def _equip_starting_gear(self) -> None:
        """Give starting equipment and auto-equip it."""
        from .items import ITEM_CLUB, ITEM_LEATHER_CAP
        # Everyone starts with a club and leather cap, already equipped
        self.equipped[EquipSlot.WEAPON.value] = ITEM_CLUB
        self.equipped[EquipSlot.HELMET.value] = ITEM_LEATHER_CAP

    # ── Computed stats ─────────────────────────────────────────────────────────

    @property
    def attack(self) -> int:
        bonus = sum(i.attack_bonus for i in self.equipped.values())
        return self._base_attack + bonus + self.temp_attack_bonus

    @property
    def defense(self) -> int:
        bonus = sum(i.defense_bonus for i in self.equipped.values())
        return self._base_defense + bonus + self.temp_defense_bonus

    @property
    def damage_reduction(self) -> int:
        """Flat damage subtracted from each incoming hit, from equipped armor/shields."""
        return sum(i.damage_reduction for i in self.equipped.values())

    @property
    def light_radius(self) -> int:
        """The player's own light reach: base vision, or more from a light source."""
        from .fov import BASE_VISION
        equipped_light = max((i.light_radius for i in self.equipped.values()), default=0)
        return max(BASE_VISION, equipped_light)

    @property
    def max_hp_bonus(self) -> int:
        """Bonus max HP from equipped accessories."""
        return sum(i.hp_bonus for i in self.equipped.values() if i.kind != ItemKind.POTION)

    @property
    def max_mp_bonus(self) -> int:
        """Bonus max MP from equipped accessories."""
        return sum(i.mp_bonus for i in self.equipped.values() if i.kind != ItemKind.POTION)

    # ── Inventory actions ──────────────────────────────────────────────────────

    def pick_up(self, item: Item) -> str:
        self.inventory.append(item)
        self.stat_items_found += 1
        if item.kind == ItemKind.TREASURE:
            msgs = []
            self.inventory.remove(item)  # treasures never sit in inventory
            if item.gold_value > 0:
                self.gold += item.gold_value
                self.stat_gold_collected += item.gold_value
                msgs.append(f"+{item.gold_value} gp")
            if item.xp_bonus:
                self.xp += item.xp_bonus
                msgs.append(f"+{item.xp_bonus} XP")
            if item.heal_on_pickup:
                healed = min(item.heal_on_pickup, self.max_hp - self.hp)
                self.hp += healed
                msgs.append(f"+{healed} HP")
            suffix = f" ({', '.join(msgs)})" if msgs else ""
            return f"Picked up {item.name}.{suffix}"
        return f"Picked up {item.name}."

    def equip(self, item: Item) -> Tuple[str, Optional[Item]]:
        """Equip an item from inventory. Returns (message, unequipped_item_or_None).

        Special routing:
        - Rings auto-fill ring_left first, then ring_right.
        - Warriors may equip a weapon into the shield slot (dual-wield).
          Equipping a shield replaces any off-hand weapon.
        """
        if item not in self.inventory:
            return "You don't have that.", None
        if item.equip_slot is None:
            return f"{item.name} cannot be equipped.", None
        if item.warrior_only and self.char_class != CharacterClass.WARRIOR:
            return f"{item.name} requires martial training — Warriors only.", None

        # ── Determine actual slot key ──────────────────────────────────────────
        if item.equip_slot == EquipSlot.RING:
            # Auto-fill left first, then right
            if EquipSlot.RING_LEFT.value not in self.equipped:
                slot = EquipSlot.RING_LEFT.value
            elif EquipSlot.RING_RIGHT.value not in self.equipped:
                slot = EquipSlot.RING_RIGHT.value
            else:
                # Both full — displace left ring
                slot = EquipSlot.RING_LEFT.value
        elif (item.equip_slot == EquipSlot.WEAPON
              and self.char_class == CharacterClass.WARRIOR
              and EquipSlot.WEAPON.value in self.equipped):
            # Warrior already has a main weapon — offer the off-hand slot
            slot = EquipSlot.SHIELD.value
        else:
            slot = item.equip_slot.value

        displaced = self.equipped.get(slot)
        if displaced:
            self.inventory.append(displaced)
        self.equipped[slot] = item
        self.inventory.remove(item)

        slot_label = _slot_label(slot)
        msg = f"Equipped {item.name} ({slot_label})."
        if displaced:
            msg += f" ({displaced.name} returned to inventory.)"
        return msg, displaced

    def unequip(self, slot: EquipSlot) -> str:
        item = self.equipped.pop(slot.value, None)
        if item is None:
            return "Nothing equipped there."
        # A lit torch is spent — it doesn't return to inventory.
        if item.light_radius > 0 and item.name == "Torch":
            return "You extinguish the torch. It crumbles to ash."
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
        if item.xp_bonus:
            self.xp += item.xp_bonus
            msgs.append(f"+{item.xp_bonus} XP")
        return f"Drank {item.name}. " + ("  ".join(msgs) if msgs else "No effect.")

    # ── Spells ─────────────────────────────────────────────────────────────────

    def cast_spell(self, spell: Spell) -> Tuple[str, int]:
        """
        Attempt to cast a spell. Returns (message, damage_dealt).
        damage_dealt is >0 only for DAMAGE spells — caller applies it to monster.
        Buffs are applied in-place here.
        """
        if spell not in self.spells:
            return "You don't know that spell.", 0
        if self.mp < spell.mp_cost:
            return f"Not enough MP to cast {spell.name}. (need {spell.mp_cost})", 0
        self.mp -= spell.mp_cost
        self.stat_mp_spent += spell.mp_cost
        if spell.effect == SpellEffect.DAMAGE:
            dmg = sum(random.randint(1, spell.damage_sides) for _ in range(spell.damage_count))
            return f"You cast {spell.name} for {dmg} damage!", dmg
        if spell.effect == SpellEffect.BUFF_DEF:
            self.temp_defense_bonus += spell.def_bonus
            self.temp_defense_turns = max(self.temp_defense_turns, spell.def_turns)
            return f"You cast {spell.name}! +{spell.def_bonus} DEF for {spell.def_turns} turns.", 0
        if spell.effect == SpellEffect.BUFF_ABSORB:
            self.damage_absorb += spell.absorb_amount
            return f"You cast {spell.name}! Absorbing up to {self.damage_absorb} damage.", 0
        if spell.effect == SpellEffect.BUFF_ATK:
            bonus = sum(random.randint(1, spell.atk_sides) for _ in range(spell.atk_count))
            self.temp_attack_bonus += bonus
            return f"You cast {spell.name}! +{bonus} ATK for next combat.", 0
        if spell.effect == SpellEffect.HEAL:
            healed = sum(random.randint(1, spell.heal_sides) for _ in range(spell.heal_count))
            healed = min(healed, self.max_hp - self.hp)
            self.hp += healed
            return f"You cast {spell.name}. +{healed} HP restored. (HP: {self.hp}/{self.max_hp})", 0
        if spell.effect == SpellEffect.TURN_UNDEAD:
            return f"You invoke {spell.name}!", 0
        if spell.effect == SpellEffect.DETECT:
            return f"You cast {spell.name}.", -1  # -1 signals caller to run detect sweep
        if spell.effect == SpellEffect.ILLUMINATE:
            return f"You cast {spell.name}! Light fills the floor.", -2  # -2 signals caller to light the floor
        if spell.effect == SpellEffect.BLINK:
            return f"You cast {spell.name}. (Blink not yet implemented.)", 0
        return f"Cast {spell.name}.", 0

    # ── Per-move tick ──────────────────────────────────────────────────────────

    def on_move(self) -> None:
        self.stat_squares_traveled += 1
        if self.mp < self.max_mp:
            self.mp = min(self.max_mp, self.mp + 1)

    # ── Level up ───────────────────────────────────────────────────────────────

    def check_level_up(self) -> Tuple[bool, List[str]]:
        """
        Check if player has enough XP to level up. If so, apply stat gains.
        Returns (did_level_up, log_messages).
        Can level up multiple times if XP is high enough.
        """
        messages = []
        leveled = False
        old_spell_count = len(self.spells)
        while self.xp >= xp_for_level(self.level + 1):
            self.level += 1
            leveled = True
            gains = _LEVEL_UP_GAINS[self.char_class]
            self.max_hp += gains["hp"]
            self.hp += gains["hp"]  # heal by the gain amount
            self._base_attack += gains["attack"]
            self._base_defense += gains["defense"]
            self.max_mp += gains["mp"]
            self.mp += gains["mp"]  # restore by the gain amount

            # Learn new spells
            self._learn_spells_for_level()

            messages.append(f"[bold green]LEVEL UP! You are now level {self.level}![/bold green]")
            parts = []
            if gains["hp"]:
                parts.append(f"+{gains['hp']} HP")
            if gains["attack"]:
                parts.append(f"+{gains['attack']} ATK")
            if gains["defense"]:
                parts.append(f"+{gains['defense']} DEF")
            if gains["mp"]:
                parts.append(f"+{gains['mp']} MP")
            if parts:
                messages.append("  " + "  ".join(parts))

        # Report new spells learned
        if leveled and len(self.spells) > old_spell_count:
            new_spells = self.spells[old_spell_count:]
            for spell in new_spells:
                messages.append(f"  [bold cyan]Learned spell: {spell.name}[/bold cyan]")

        return leveled, messages

    # ── Helpers ────────────────────────────────────────────────────────────────

    @property
    def invuln_active(self) -> bool:
        return self.invuln_turns_remaining > 0

    def tick_buffs(self) -> None:
        """Advance timed buffs by one turn. Clears flat DEF when its timer expires."""
        if self.temp_defense_turns > 0:
            self.temp_defense_turns -= 1
            if self.temp_defense_turns == 0:
                self.temp_defense_bonus = 0

    def use_scroll(self, item: "Item") -> Tuple[str, int]:
        """
        Use a scroll from inventory. Returns (message, fireball_damage).
        fireball_damage > 0 only for Scroll of Fireball — caller applies to monster.
        Consumes the scroll.
        """
        from .items import ItemKind
        if item.kind != ItemKind.SCROLL:
            return f"{item.name} is not a scroll.", 0
        if item not in self.inventory:
            return "You don't have that.", 0
        self.inventory.remove(item)
        if item.invuln_turns:
            self.invuln_turns_remaining += item.invuln_turns
            return f"You read {item.name}! Invulnerable for {item.invuln_turns} rounds!", 0
        if item.light_radius:
            # Caller reads light_radius off the item to light the floor.
            return f"You read {item.name}! Light floods the floor.", 0
        if item.hp_bonus:
            healed = min(item.hp_bonus, self.max_hp - self.hp)
            self.hp += healed
            return f"You read {item.name}! +{healed} HP restored. (HP: {self.hp}/{self.max_hp})", 0
        if item.damage_count and item.damage_sides:
            dmg = sum(random.randint(1, item.damage_sides) for _ in range(item.damage_count))
            return f"You read {item.name}! A bolt of fire erupts for {dmg} damage!", dmg
        return f"You read {item.name}. Nothing happens.", 0

    @property
    def rage_active(self) -> bool:
        return self.char_class == CharacterClass.WARRIOR and self.rage_turns_remaining > 0

    def activate_rage(self) -> str:
        """Warrior activates Rage: 3 turns of double damage, once per floor."""
        if self.char_class != CharacterClass.WARRIOR:
            return "Only Warriors can Rage."
        if self.rage_used_this_floor:
            return "You have already raged this floor."
        self.rage_turns_remaining = 3
        self.rage_used_this_floor = True
        return "[bold red]RAGE![/bold red] Your attacks deal double damage for 3 turns!"

    @property
    def trap_detect_chance(self) -> float:
        """Thief only: cumulative 10% per level chance to detect traps (max 100%)."""
        if self.char_class != CharacterClass.THIEF:
            return 0.0
        return min(self.level * 0.10, 1.0)

    @property
    def trap_disarm_chance(self) -> float:
        """Thief only: cumulative 10% per level chance to disarm a detected trap."""
        if self.char_class != CharacterClass.THIEF:
            return 0.0
        return min(self.level * 0.10, 1.0)

    @property
    def has_mp(self) -> bool:
        return self.max_mp > 0

    def equipped_in(self, slot: EquipSlot) -> Optional[Item]:
        return self.equipped.get(slot.value)

    @property
    def xp_to_next_level(self) -> int:
        """Return XP needed for next level, or 0 if at max tracked level."""
        return max(0, xp_for_level(self.level + 1) - self.xp)

    @property
    def is_dual_wielding(self) -> bool:
        """True when a Warrior has a weapon in both the main and off-hand (shield) slots."""
        if self.char_class != CharacterClass.WARRIOR:
            return False
        off_hand = self.equipped.get(EquipSlot.SHIELD.value)
        return off_hand is not None and off_hand.equip_slot == EquipSlot.WEAPON

    @property
    def off_hand_weapon(self) -> Optional[Item]:
        """Return the off-hand weapon when dual-wielding, else None."""
        if not self.is_dual_wielding:
            return None
        return self.equipped.get(EquipSlot.SHIELD.value)
