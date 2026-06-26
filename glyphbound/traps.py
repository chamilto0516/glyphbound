from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple


class TrapKind(Enum):
    SNAP_TRAP      = "Snap Trap"
    FLAME_WARD     = "Flame Ward"
    FLOOR_SPIKES   = "Floor Spikes"
    CRUSHING_ROCKS = "Crushing Rockfall"


@dataclass
class Trap:
    kind:         TrapKind
    name:         str
    damage_dice:  int
    damage_sides: int
    is_detected:  bool = False
    is_magic:     bool = False  # detectable by Detect Magic
    glyph:        str  = "T"

    def trigger(self) -> Tuple[int, str]:
        dmg = sum(random.randint(1, self.damage_sides) for _ in range(self.damage_dice))
        return dmg, f"  {self.name} triggered! You take {dmg} damage!"


def make_snap_trap() -> Trap:
    return Trap(kind=TrapKind.SNAP_TRAP, name="Snap Trap",
                damage_dice=1, damage_sides=4)

def make_flame_ward() -> Trap:
    return Trap(kind=TrapKind.FLAME_WARD, name="Flame Ward",
                damage_dice=1, damage_sides=10, is_magic=True)

def make_floor_spikes() -> Trap:
    return Trap(kind=TrapKind.FLOOR_SPIKES, name="Floor Spikes",
                damage_dice=1, damage_sides=8)

def make_crushing_rockfall() -> Trap:
    return Trap(kind=TrapKind.CRUSHING_ROCKS, name="Crushing Rockfall",
                damage_dice=1, damage_sides=10)


TRAP_MAKERS = [make_snap_trap, make_flame_ward, make_floor_spikes, make_crushing_rockfall]
