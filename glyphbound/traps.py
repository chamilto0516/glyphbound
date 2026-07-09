from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from .status_effects import EffectType


class TrapKind(Enum):
    SNAP_TRAP      = "Snap Trap"
    FLAME_WARD     = "Flame Ward"
    FLOOR_SPIKES   = "Floor Spikes"
    CRUSHING_ROCKS = "Crushing Rockfall"
    POISON_NEEDLE  = "Poison Needle"
    STUN_TRAP      = "Stun Trap"
    WEB_TRAP       = "Web Trap"
    SILENCE_TRAP   = "Silence Trap"


@dataclass
class Trap:
    kind:         TrapKind
    name:         str
    damage_dice:  int
    damage_sides: int
    is_detected:  bool = False
    is_magic:     bool = False  # detectable by Detect Magic
    glyph:        str  = "T"
    applies_effect: Optional[Tuple[EffectType, int, int]] = None  # (type, duration, potency)

    def trigger(self) -> Tuple[int, str]:
        dmg = sum(random.randint(1, self.damage_sides) for _ in range(self.damage_dice))
        msg = f"  {self.name} triggered!"
        if dmg > 0:
            msg += f" You take {dmg} damage!"
        return dmg, msg


def make_snap_trap() -> Trap:
    return Trap(kind=TrapKind.SNAP_TRAP, name="Snap Trap",
                damage_dice=1, damage_sides=4)

def make_flame_ward() -> Trap:
    return Trap(kind=TrapKind.FLAME_WARD, name="Flame Ward",
                damage_dice=1, damage_sides=10, is_magic=True,
                applies_effect=(EffectType.BURNING, 2, 2))

def make_floor_spikes() -> Trap:
    return Trap(kind=TrapKind.FLOOR_SPIKES, name="Floor Spikes",
                damage_dice=1, damage_sides=8)

def make_crushing_rockfall() -> Trap:
    return Trap(kind=TrapKind.CRUSHING_ROCKS, name="Crushing Rockfall",
                damage_dice=1, damage_sides=10)


def make_poison_needle() -> Trap:
    return Trap(kind=TrapKind.POISON_NEEDLE, name="Poison Needle",
                damage_dice=0, damage_sides=0,
                applies_effect=(EffectType.POISONED, 5, 2))


def make_stun_trap() -> Trap:
    return Trap(kind=TrapKind.STUN_TRAP, name="Stun Trap",
                damage_dice=1, damage_sides=4,
                applies_effect=(EffectType.STUNNED, 1, 0))


def make_web_trap() -> Trap:
    return Trap(kind=TrapKind.WEB_TRAP, name="Web Trap",
                damage_dice=0, damage_sides=0,
                applies_effect=(EffectType.BOUND, 3, 0))


def make_silence_trap() -> Trap:
    return Trap(kind=TrapKind.SILENCE_TRAP, name="Silence Trap",
                damage_dice=0, damage_sides=0, is_magic=True,
                applies_effect=(EffectType.SILENCED, 4, 0))


TRAP_MAKERS = [
    make_snap_trap,
    make_flame_ward,
    make_floor_spikes,
    make_crushing_rockfall,
    make_poison_needle,
    make_stun_trap,
    make_web_trap,
    make_silence_trap,
]
