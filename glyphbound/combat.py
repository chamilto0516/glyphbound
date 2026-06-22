from __future__ import annotations

import random
from typing import List, Optional, Tuple

from .items import Item, EquipSlot
from .monsters import Monster
from .player import Player
from .spells import Spell, SpellEffect


def roll_damage(weapon: Item | None) -> int:
    if weapon is None:
        return 1  # unarmed: 1 static
    if weapon.damage_sides == 0:
        return weapon.damage_count
    return sum(random.randint(1, weapon.damage_sides) for _ in range(weapon.damage_count))


def _best_damage_spell(player: Player) -> Optional[Spell]:
    """Return the highest expected-damage spell the player can currently afford."""
    candidates = [
        s for s in player.spells
        if s.effect == SpellEffect.DAMAGE and player.mp >= s.mp_cost
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda s: s.damage_sides * s.damage_count)


def _attacker_hits(attack_roll: int, defense: int) -> bool:
    return attack_roll > defense


def resolve_combat(player: Player, monster: Monster) -> Tuple[List[str], bool]:
    """
    Run combat to completion. Player always strikes first each round.
    Wizards cast their best affordable damage spell each round; all other
    classes use their equipped weapon.
    Returns (log_lines, player_survived).
    xp and hp changes are applied directly to player and monster.
    """
    from .player import CharacterClass
    log: List[str] = []
    player_weapon = player.equipped.get(EquipSlot.WEAPON.value)
    is_wizard = player.char_class == CharacterClass.WIZARD

    log.append(f"You attack the {monster.name}!")

    while player.hp > 0 and monster.hp > 0:
        # ── Player attacks ────────────────────────────────────────────────────
        spell = _best_damage_spell(player) if is_wizard else None
        if spell:
            msg, dmg = player.cast_spell(spell)
            monster.hp = max(0, monster.hp - dmg)
            log.append(f"  {msg}  {monster.name} HP: {monster.hp}/{monster.max_hp}")
        else:
            p_roll = random.randint(1, 6) + player.attack
            if _attacker_hits(p_roll, monster.defense):
                dmg = roll_damage(player_weapon)
                monster.hp = max(0, monster.hp - dmg)
                wpn_name = player_weapon.name if player_weapon else "fists"
                log.append(f"  Your {wpn_name} hits for {dmg}! {monster.name} HP: {monster.hp}/{monster.max_hp}")
            else:
                log.append(f"  Your attack misses the {monster.name}.")

        if monster.hp == 0:
            break

        # ── Monster attacks ───────────────────────────────────────────────────
        m_roll = random.randint(1, 6) + monster.attack
        if _attacker_hits(m_roll, player.defense):
            dmg = roll_damage(monster.weapon)
            player.hp = max(0, player.hp - dmg)
            wpn_name = monster.weapon.name if monster.weapon else "claws"
            log.append(f"  {monster.name} hits you with {wpn_name} for {dmg}! Your HP: {player.hp}/{player.max_hp}")
        else:
            log.append(f"  {monster.name} misses you.")

    player.temp_defense_bonus = 0  # Magic Armor expires after each combat

    if monster.hp == 0:
        player.xp += monster.xp_value
        log.append(f"You defeated the {monster.name}! +{monster.xp_value} XP")
        return log, True
    else:
        log.append(f"You have been slain by the {monster.name}...")
        return log, False
