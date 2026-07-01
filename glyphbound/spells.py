from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .fov import SPELL_RADIUS


class SpellEffect(Enum):
    DAMAGE      = "damage"      # deals direct damage to target monster
    BUFF_DEF    = "buff_def"    # raises caster defense by a flat amount for a few turns
    BUFF_ABSORB = "buff_absorb" # grants a finite pool that soaks incoming damage
    BUFF_ATK    = "buff_atk"    # raises caster attack for next combat
    HEAL        = "heal"        # restores caster HP
    TURN_UNDEAD = "turn_undead" # destroys weak undead, damages strong undead
    DETECT      = "detect"      # reveals items/monsters in nearby rooms
    BLINK       = "blink"       # teleport short distance (escape combat)
    ILLUMINATE  = "illuminate"  # lights the whole floor for its duration


@dataclass
class Spell:
    name: str
    mp_cost: int
    effect: SpellEffect
    min_level: int    = 1   # minimum character level to learn this spell
    damage_sides: int = 0
    damage_count: int = 1
    def_sides: int    = 0
    def_count: int    = 1
    def_bonus: int    = 0   # BUFF_DEF: flat DEF granted
    def_turns: int    = 0   # BUFF_DEF: turns the flat DEF lasts
    absorb_amount: int = 0  # BUFF_ABSORB: damage the pool soaks
    atk_sides: int    = 0
    atk_count: int    = 1
    heal_sides: int   = 0
    heal_count: int   = 1
    light_radius: int = 0   # ILLUMINATE: tiles lit for the floor
    description: str  = ""

    def damage_label(self) -> str:
        if self.effect == SpellEffect.DAMAGE:
            return f"{self.damage_count}d{self.damage_sides}"
        if self.effect == SpellEffect.BUFF_DEF:
            return f"+{self.def_bonus} DEF ({self.def_turns}t)"
        if self.effect == SpellEffect.BUFF_ABSORB:
            return f"absorb {self.absorb_amount}"
        if self.effect == SpellEffect.BUFF_ATK:
            return f"+{self.atk_count}d{self.atk_sides} ATK"
        if self.effect == SpellEffect.HEAL:
            return f"+{self.heal_count}d{self.heal_sides} HP"
        if self.effect == SpellEffect.TURN_UNDEAD:
            return "turns undead"
        if self.effect == SpellEffect.DETECT:
            return "detect"
        if self.effect == SpellEffect.BLINK:
            return "blink"
        if self.effect == SpellEffect.ILLUMINATE:
            return "illuminate"
        return ""


# ── Wizard spells ──────────────────────────────────────────────────────────────

SPELL_MAGIC_BOLT = Spell(
    name="Magic Bolt",
    mp_cost=2,
    effect=SpellEffect.DAMAGE,
    min_level=1,
    damage_sides=6, damage_count=1,
    description="A bolt of arcane energy. 1d6 damage.",
)

SPELL_MAGIC_ARMOR = Spell(
    name="Magic Armor",
    mp_cost=3,
    effect=SpellEffect.BUFF_DEF,
    min_level=1,
    def_bonus=2, def_turns=3,
    description="Conjures a shield of force. +2 DEF for 3 turns.",
)

SPELL_DETECT_MAGIC = Spell(
    name="Detect Magic",
    mp_cost=2,
    effect=SpellEffect.DETECT,
    min_level=1,
    description="Reveals hidden items and monsters in nearby rooms.",
)

SPELL_BLINK = Spell(
    name="Blink",
    mp_cost=4,
    effect=SpellEffect.BLINK,
    min_level=1,
    description="Teleport 3-5 tiles away. Can escape combat.",
)

SPELL_FIREBALL = Spell(
    name="Fireball",
    mp_cost=5,
    effect=SpellEffect.DAMAGE,
    min_level=2,
    damage_sides=10, damage_count=1,
    description="A burst of fire. 1d10 damage.",
)

SPELL_ILLUMINATION = Spell(
    name="Illumination",
    mp_cost=4,
    effect=SpellEffect.ILLUMINATE,
    min_level=2,
    light_radius=SPELL_RADIUS,
    description="Conjures magical light that fills the floor.",
)

SPELL_LIGHTNING_BOLT = Spell(
    name="Lightning Bolt",
    mp_cost=6,
    effect=SpellEffect.DAMAGE,
    min_level=3,
    damage_sides=6, damage_count=2,
    description="Crackling electricity. 2d6 damage.",
)

SPELL_SHIELD = Spell(
    name="Shield",
    mp_cost=5,
    effect=SpellEffect.BUFF_ABSORB,
    min_level=4,
    absorb_amount=15,
    description="A powerful barrier that absorbs 15 damage.",
)

SPELL_METEOR_SWARM = Spell(
    name="Meteor Swarm",
    mp_cost=8,
    effect=SpellEffect.DAMAGE,
    min_level=5,
    damage_sides=8, damage_count=3,
    description="Raining fire from above. 3d8 damage.",
)

SPELL_ARCANE_BLAST = Spell(
    name="Arcane Blast",
    mp_cost=10,
    effect=SpellEffect.DAMAGE,
    min_level=6,
    damage_sides=10, damage_count=3,
    description="Pure magical destruction. 3d10 damage.",
)

SPELL_TIME_STOP = Spell(
    name="Time Stop",
    mp_cost=12,
    effect=SpellEffect.BUFF_ABSORB,
    min_level=7,
    absorb_amount=25,
    description="Bend time itself. Absorbs 25 damage.",
)

WIZARD_SPELLS = [
    SPELL_MAGIC_BOLT,
    SPELL_MAGIC_ARMOR,
    SPELL_DETECT_MAGIC,
    SPELL_BLINK,
    SPELL_FIREBALL,
    SPELL_ILLUMINATION,
    SPELL_LIGHTNING_BOLT,
    SPELL_SHIELD,
    SPELL_METEOR_SWARM,
    SPELL_ARCANE_BLAST,
    SPELL_TIME_STOP,
]

# ── Cleric spells ──────────────────────────────────────────────────────────────

SPELL_HEAL = Spell(
    name="Heal",
    mp_cost=4,
    effect=SpellEffect.HEAL,
    min_level=1,
    heal_sides=6, heal_count=2,
    description="Divine mending. Restores 2d6 HP.",
)

SPELL_SMITE = Spell(
    name="Smite",
    mp_cost=3,
    effect=SpellEffect.DAMAGE,
    min_level=1,
    damage_sides=8, damage_count=1,
    description="A blessed strike. 1d8 holy damage.",
)

SPELL_BLESS = Spell(
    name="Bless",
    mp_cost=3,
    effect=SpellEffect.BUFF_ATK,
    min_level=1,
    atk_sides=6, atk_count=1,
    description="Divine favor. +1d6 ATK for next combat.",
)

SPELL_SANCTUARY = Spell(
    name="Sanctuary",
    mp_cost=4,
    effect=SpellEffect.BUFF_DEF,
    min_level=1,
    def_bonus=2, def_turns=3,
    description="Divine protection. +2 DEF for 3 turns.",
)

SPELL_TURN_UNDEAD = Spell(
    name="Turn Undead",
    mp_cost=5,
    effect=SpellEffect.TURN_UNDEAD,
    min_level=2,
    description="Destroys weak undead outright; heavily damages the strong.",
)

SPELL_LIGHT_FROM_HEAVEN = Spell(
    name="Light from Heaven",
    mp_cost=6,
    effect=SpellEffect.DAMAGE,
    min_level=3,
    damage_sides=8, damage_count=2,
    description="Searing radiance. 2d8 holy damage.",
)

SPELL_GREATER_HEAL = Spell(
    name="Greater Heal",
    mp_cost=7,
    effect=SpellEffect.HEAL,
    min_level=4,
    heal_sides=6, heal_count=4,
    description="Powerful divine restoration. Restores 4d6 HP.",
)

SPELL_DIVINE_SHIELD = Spell(
    name="Divine Shield",
    mp_cost=6,
    effect=SpellEffect.BUFF_ABSORB,
    min_level=5,
    absorb_amount=12,
    description="Impenetrable holy barrier that absorbs 12 damage.",
)

SPELL_HOLY_FIRE = Spell(
    name="Holy Fire",
    mp_cost=9,
    effect=SpellEffect.DAMAGE,
    min_level=6,
    damage_sides=10, damage_count=3,
    description="Righteous flames. 3d10 holy damage.",
)

SPELL_WRATH_OF_HEAVEN = Spell(
    name="Wrath of Heaven",
    mp_cost=10,
    effect=SpellEffect.DAMAGE,
    min_level=7,
    damage_sides=8, damage_count=4,
    description="Ultimate divine judgment. 4d8 holy damage.",
)

CLERIC_SPELLS = [
    SPELL_HEAL,
    SPELL_SMITE,
    SPELL_BLESS,
    SPELL_SANCTUARY,
    SPELL_TURN_UNDEAD,
    SPELL_LIGHT_FROM_HEAVEN,
    SPELL_GREATER_HEAL,
    SPELL_DIVINE_SHIELD,
    SPELL_HOLY_FIRE,
    SPELL_WRATH_OF_HEAVEN,
]
