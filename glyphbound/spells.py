from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SpellEffect(Enum):
    DAMAGE      = "damage"      # deals direct damage to target monster
    BUFF_DEF    = "buff_def"    # raises caster defense for next combat
    HEAL        = "heal"        # restores caster HP
    TURN_UNDEAD = "turn_undead" # destroys weak undead, damages strong undead


@dataclass
class Spell:
    name: str
    mp_cost: int
    effect: SpellEffect
    damage_sides: int = 0
    damage_count: int = 1
    def_sides: int    = 0
    def_count: int    = 1
    heal_sides: int   = 0
    heal_count: int   = 1
    description: str  = ""

    def damage_label(self) -> str:
        if self.effect == SpellEffect.DAMAGE:
            return f"{self.damage_count}d{self.damage_sides}"
        if self.effect == SpellEffect.BUFF_DEF:
            return f"+{self.def_count}d{self.def_sides} DEF"
        if self.effect == SpellEffect.HEAL:
            return f"+{self.heal_count}d{self.heal_sides} HP"
        if self.effect == SpellEffect.TURN_UNDEAD:
            return "turns undead"
        return ""


# ── Wizard spells ──────────────────────────────────────────────────────────────

SPELL_MAGIC_BOLT = Spell(
    name="Magic Bolt",
    mp_cost=2,
    effect=SpellEffect.DAMAGE,
    damage_sides=6, damage_count=1,
    description="A bolt of arcane energy. 1d6 damage.",
)

SPELL_FIREBALL = Spell(
    name="Fireball",
    mp_cost=5,
    effect=SpellEffect.DAMAGE,
    damage_sides=10, damage_count=1,
    description="A burst of fire. 1d10 damage.",
)

SPELL_MAGIC_ARMOR = Spell(
    name="Magic Armor",
    mp_cost=3,
    effect=SpellEffect.BUFF_DEF,
    def_sides=10, def_count=1,
    description="Conjures a shield of force. +1d10 DEF for next combat.",
)

WIZARD_SPELLS = [SPELL_MAGIC_BOLT, SPELL_FIREBALL, SPELL_MAGIC_ARMOR]

# ── Cleric spells ──────────────────────────────────────────────────────────────

SPELL_HEAL = Spell(
    name="Heal",
    mp_cost=4,
    effect=SpellEffect.HEAL,
    heal_sides=6, heal_count=2,
    description="Divine mending. Restores 2d6 HP.",
)

SPELL_SMITE = Spell(
    name="Smite",
    mp_cost=3,
    effect=SpellEffect.DAMAGE,
    damage_sides=8, damage_count=1,
    description="A blessed strike. 1d8 holy damage.",
)

SPELL_LIGHT_FROM_HEAVEN = Spell(
    name="Light from Heaven",
    mp_cost=6,
    effect=SpellEffect.DAMAGE,
    damage_sides=8, damage_count=2,
    description="Searing radiance. 2d8 holy damage.",
)

SPELL_TURN_UNDEAD = Spell(
    name="Turn Undead",
    mp_cost=5,
    effect=SpellEffect.TURN_UNDEAD,
    description="Destroys weak undead outright; heavily damages the strong.",
)

CLERIC_SPELLS = [SPELL_HEAL, SPELL_SMITE, SPELL_LIGHT_FROM_HEAVEN, SPELL_TURN_UNDEAD]
