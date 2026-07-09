from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .player import Player
    from .monsters import Monster


class EffectType(Enum):
    """Types of status effects that can be applied to entities."""
    POISONED = "poisoned"
    STUNNED = "stunned"
    BURNING = "burning"
    BOUND = "bound"
    SILENCED = "silenced"


@dataclass
class StatusEffect:
    """A timed status effect on an entity.

    Stored in entity.status_effects dict, keyed by EffectType.
    Reapplying an effect refreshes duration/potency to max.
    """
    effect_type: EffectType
    duration: int          # turns remaining
    potency: int = 0       # damage/tick, penalty magnitude, etc.
    source: str = ""       # descriptive: "spider bite", "Flame Ward", etc.


def apply_effect(entity, effect: StatusEffect) -> str:
    """Apply a status effect to an entity (Player or Monster).

    If the effect already exists, refresh duration and potency to max values.
    Returns a log message describing the application.
    """
    if not hasattr(entity, 'status_effects'):
        # Safety: entity doesn't support status effects yet
        return ""

    etype = effect.effect_type

    if etype in entity.status_effects:
        # Refresh: take max of existing and new duration/potency
        existing = entity.status_effects[etype]
        existing.duration = max(existing.duration, effect.duration)
        existing.potency = max(existing.potency, effect.potency)
        return f"[yellow]{entity.name if hasattr(entity, 'name') else 'You'} {etype.value} effect refreshed![/yellow]"
    else:
        # New application
        entity.status_effects[etype] = effect
        effect_msg = {
            EffectType.POISONED: "poisoned",
            EffectType.STUNNED: "stunned",
            EffectType.BURNING: "burning",
            EffectType.BOUND: "bound",
            EffectType.SILENCED: "silenced",
        }
        name = entity.name if hasattr(entity, 'name') else "You"
        msg = effect_msg.get(etype, etype.value)
        return f"[yellow]{name} is {msg}![/yellow]"


def remove_effect(entity, effect_type: EffectType) -> str:
    """Remove a status effect from an entity.

    Returns a log message if the effect was present, empty string otherwise.
    """
    if not hasattr(entity, 'status_effects'):
        return ""

    if effect_type in entity.status_effects:
        del entity.status_effects[effect_type]
        name = entity.name if hasattr(entity, 'name') else "You"
        cured_msg = {
            EffectType.POISONED: "cured of poison",
            EffectType.STUNNED: "recovered from stun",
            EffectType.BURNING: "no longer burning",
            EffectType.BOUND: "freed from binding",
            EffectType.SILENCED: "can speak again",
        }
        msg = cured_msg.get(effect_type, f"recovered from {effect_type.value}")
        return f"[green]{name} is {msg}![/green]"
    return ""


def remove_all_effects(entity) -> None:
    """Clear all status effects from an entity."""
    if hasattr(entity, 'status_effects'):
        entity.status_effects.clear()


def has_effect(entity, effect_type: EffectType) -> bool:
    """Check if an entity has a specific status effect active."""
    if not hasattr(entity, 'status_effects'):
        return False
    return effect_type in entity.status_effects


def tick_effects(entity) -> List[str]:
    """Process status effects at the start of an entity's turn.

    Deals damage-over-time, decrements durations, removes expired effects.
    Returns log messages for each effect that triggers.
    """
    if not hasattr(entity, 'status_effects'):
        return []

    log: List[str] = []
    expired: List[EffectType] = []

    for etype, effect in list(entity.status_effects.items()):
        name = entity.name if hasattr(entity, 'name') else "You"

        # Apply effect behavior
        if etype == EffectType.POISONED:
            entity.hp = max(0, entity.hp - effect.potency)
            log.append(f"[green]{name} takes {effect.potency} poison damage! HP: {entity.hp}/{entity.max_hp}[/green]")

        elif etype == EffectType.BURNING:
            entity.hp = max(0, entity.hp - effect.potency)
            log.append(f"[bright_red]{name} takes {effect.potency} fire damage from burning! HP: {entity.hp}/{entity.max_hp}[/bright_red]")

        # Decrement duration
        effect.duration -= 1
        if effect.duration <= 0:
            expired.append(etype)

    # Remove expired effects
    for etype in expired:
        del entity.status_effects[etype]
        name = entity.name if hasattr(entity, 'name') else "You"
        fade_msg = {
            EffectType.POISONED: "poison fades",
            EffectType.STUNNED: "recovered from stun",
            EffectType.BURNING: "fire goes out",
            EffectType.BOUND: "breaks free",
            EffectType.SILENCED: "can speak again",
        }
        msg = fade_msg.get(etype, f"{etype.value} fades")
        log.append(f"[dim]{name}'s {msg}.[/dim]")

    return log


def can_move(entity) -> Tuple[bool, List[str]]:
    """Check if an entity can move this turn.

    Blocked by: STUNNED, BOUND
    Returns (can_move, log_messages)
    """
    if not hasattr(entity, 'status_effects'):
        return True, []

    name = entity.name if hasattr(entity, 'name') else "You"

    if EffectType.STUNNED in entity.status_effects:
        return False, [f"[yellow]{name} is stunned and cannot act![/yellow]"]

    if EffectType.BOUND in entity.status_effects:
        return False, [f"[bright_magenta]{name} is bound and cannot move![/bright_magenta]"]

    return True, []


def can_attack(entity) -> Tuple[bool, List[str]]:
    """Check if an entity can attack this turn.

    Blocked by: STUNNED
    Returns (can_attack, log_messages)
    """
    if not hasattr(entity, 'status_effects'):
        return True, []

    name = entity.name if hasattr(entity, 'name') else "You"

    if EffectType.STUNNED in entity.status_effects:
        return False, [f"[yellow]{name} is stunned and cannot act![/yellow]"]

    return True, []


def can_cast(entity) -> Tuple[bool, List[str]]:
    """Check if an entity can cast spells this turn.

    Blocked by: STUNNED, SILENCED
    Returns (can_cast, log_messages)
    """
    if not hasattr(entity, 'status_effects'):
        return True, []

    name = entity.name if hasattr(entity, 'name') else "You"

    if EffectType.STUNNED in entity.status_effects:
        return False, [f"[yellow]{name} is stunned and cannot act![/yellow]"]

    if EffectType.SILENCED in entity.status_effects:
        return False, [f"[dim]{name} is silenced and cannot cast spells![/dim]"]

    return True, []


def get_defense_penalty(entity) -> int:
    """Get the defense penalty from active status effects.

    BURNING: -1 DEF
    """
    if not hasattr(entity, 'status_effects'):
        return 0

    penalty = 0
    if EffectType.BURNING in entity.status_effects:
        penalty += 1

    return penalty
