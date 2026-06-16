from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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
    attack: int  = 0
    defense: int = 0
    xp: int      = 0
    level: int   = 1
    mp: int      = 0
    max_mp: int  = 0

    def __post_init__(self) -> None:
        stats = _CLASS_STATS[self.char_class]
        self.max_hp  = stats["hp"]
        self.hp      = stats["hp"]
        self.attack  = stats["attack"]
        self.defense = stats["defense"]
        self.max_mp  = stats["mp"]
        self.mp      = stats["mp"]

    def on_move(self) -> None:
        # Wizard MP trickles back as they explore; Cleric regen to be tuned with spells
        if self.mp < self.max_mp:
            self.mp = min(self.max_mp, self.mp + 1)

    @property
    def has_mp(self) -> bool:
        return self.max_mp > 0
