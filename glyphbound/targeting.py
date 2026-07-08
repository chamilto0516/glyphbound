from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Literal, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .items import Item
    from .monsters import Monster
    from .spells import Spell


class TargetShape(Enum):
    SINGLE = "single"  # must resolve to a monster tile; empty tile is a fizzle, not invalid
    POINT  = "point"   # AOE centered on any chosen point in range/LOS (may be a monster's tile)
    SELF   = "self"    # AOE centered on the caster; no cursor step


@dataclass
class PendingRangedAction:
    kind: Literal["spell", "thrown_weapon", "ranged_weapon"]
    spell: Optional["Spell"] = None
    item: Optional["Item"] = None
    label: str = ""


@dataclass
class TargetingSession:
    action: PendingRangedAction
    shape: TargetShape
    max_range: int = 0  # Chebyshev distance; 0 = unlimited within FOV
    aoe_radius: int = 0
    cursor_x: int = 0
    cursor_y: int = 0
    monster_cycle: List[Tuple[Tuple[int, int], "Monster"]] = field(default_factory=list)
    cycle_index: int = -1
