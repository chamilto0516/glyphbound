from __future__ import annotations

import random
from typing import List, Optional, Tuple

from .items import Item, EquipSlot
from .monsters import Monster
from .player import Player
from .spells import Spell, SpellEffect

TURN_UNDEAD_WEAK_THRESHOLD = 10  # max_hp at or below this → destroyed outright


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


def execute_player_attack(player: Player, monster: Monster) -> List[str]:
    """Execute one player weapon attack round. Mutates monster.hp. Returns log lines."""
    from .player import CharacterClass
    log: List[str] = []
    player_weapon = player.equipped.get(EquipSlot.WEAPON.value)
    spell = _best_damage_spell(player) if player.char_class == CharacterClass.WIZARD else None
    if spell:
        msg, dmg = player.cast_spell(spell)
        monster.hp = max(0, monster.hp - dmg)
        log.append(f"  {msg}  {monster.name} HP: {monster.hp}/{monster.max_hp}")
    else:
        p_roll = random.randint(1, 6) + player.attack
        if _attacker_hits(p_roll, monster.defense):
            dmg = roll_damage(player_weapon)
            wpn_name = player_weapon.name if player_weapon else "fists"
            backstab = (
                player.char_class == CharacterClass.THIEF
                and random.random() < player.level * 0.10
            )
            if backstab:
                dmg *= 2
                monster.hp = max(0, monster.hp - dmg)
                log.append(f"  [bold yellow]BACKSTAB![/bold yellow] Your {wpn_name} strikes a vital spot for {dmg}! {monster.name} HP: {monster.hp}/{monster.max_hp}")
            else:
                monster.hp = max(0, monster.hp - dmg)
                log.append(f"  Your {wpn_name} hits for {dmg}! {monster.name} HP: {monster.hp}/{monster.max_hp}")
        else:
            log.append(f"  Your attack misses the {monster.name}.")
    return log


def execute_monster_attack(player: Player, monster: Monster) -> List[str]:
    """Execute one monster attack round. Mutates player.hp. Returns log lines."""
    log: List[str] = []
    m_roll = random.randint(1, 6) + monster.attack
    if _attacker_hits(m_roll, player.defense):
        dmg = roll_damage(monster.weapon)
        player.hp = max(0, player.hp - dmg)
        player.stat_damage_taken += dmg
        wpn_name = monster.weapon.name if monster.weapon else "claws"
        log.append(f"  {monster.name} hits you with {wpn_name} for {dmg}! Your HP: {player.hp}/{player.max_hp}")
    else:
        log.append(f"  {monster.name} misses you.")
    return log


def execute_flee_attempt(player: Player, monster: Monster) -> Tuple[List[str], bool]:
    """Flee attempt. Thief: min 50% + 5%/level (cap 100%). Others: 25%. On failure, monster attacks."""
    from .player import CharacterClass
    log: List[str] = []
    if player.char_class == CharacterClass.THIEF:
        chance = min(0.50 + player.level * 0.05, 1.0)
    else:
        chance = 0.25
    if random.random() < chance:
        log.append(f"You flee from the {monster.name}!")
        return log, True
    log.append(f"You try to flee but {monster.name} blocks your way!")
    log.extend(execute_monster_attack(player, monster))
    return log, False


def resolve_combat(player: Player, monster: Monster) -> Tuple[List[str], bool, List[Item]]:
    """
    Run combat to completion. Player always strikes first each round.
    Wizards cast their best affordable damage spell each round; all other
    classes use their equipped weapon.
    Returns (log_lines, player_survived, loot_drops).
    xp and hp changes are applied directly to player and monster.
    """
    log: List[str] = []
    log.append(f"You attack the {monster.name}!")

    while player.hp > 0 and monster.hp > 0:
        log.extend(execute_player_attack(player, monster))
        if monster.hp == 0:
            break
        log.extend(execute_monster_attack(player, monster))

    player.temp_defense_bonus = 0  # buffs expire after each combat
    player.temp_attack_bonus = 0

    loot: List[Item] = []
    if monster.hp == 0:
        player.xp += monster.xp_value
        player.stat_monsters_killed += 1
        log.append(f"You defeated the {monster.name}! +{monster.xp_value} XP")
        leveled, level_msgs = player.check_level_up()
        if leveled:
            log.extend(level_msgs)
        # Generate loot
        loot = monster.drop_loot()
        if loot:
            loot_names = ", ".join(item.name for item in loot)
            log.append(f"  {monster.name} dropped: {loot_names}")
        return log, True, loot
    else:
        log.append(f"You have been slain by the {monster.name}...")
        return log, False, []


def apply_spell_to_monster(
    player: Player,
    spell: Spell,
    monster: Monster,
) -> Tuple[List[str], bool, List[Item]]:
    """
    Apply a single out-of-combat spell to a monster.
    Returns (log_lines, monster_killed, loot_drops).
    Mutates monster.hp and player.xp in-place.
    Caller must call dungeon.remove_monster() when monster_killed is True.
    """
    log: List[str] = []

    if spell.effect == SpellEffect.DAMAGE:
        msg, dmg = player.cast_spell(spell)
        log.append(msg)
        if dmg:
            monster.hp = max(0, monster.hp - dmg)
            log.append(f"  {monster.name} takes {dmg} damage! HP: {monster.hp}/{monster.max_hp}")

    elif spell.effect == SpellEffect.TURN_UNDEAD:
        if not monster.is_undead:
            log.append(f"Turn Undead has no effect on {monster.name}.")
            return log, False, []
        msg, _ = player.cast_spell(spell)
        log.append(msg)
        if monster.max_hp <= TURN_UNDEAD_WEAK_THRESHOLD:
            monster.hp = 0
            log.append(f"  {monster.name} crumbles to dust!")
        else:
            dmg = random.randint(monster.max_hp // 2, monster.max_hp - 1)
            monster.hp = max(0, monster.hp - dmg)
            log.append(f"  {monster.name} takes {dmg} damage! HP: {monster.hp}/{monster.max_hp}")

    killed = monster.hp == 0
    loot: List[Item] = []
    if killed:
        player.xp += monster.xp_value
        player.stat_monsters_killed += 1
        log.append(f"  {monster.name} is slain! +{monster.xp_value} XP")
        leveled, level_msgs = player.check_level_up()
        if leveled:
            log.extend(level_msgs)
        # Generate loot
        loot = monster.drop_loot()
        if loot:
            loot_names = ", ".join(item.name for item in loot)
            log.append(f"  {monster.name} dropped: {loot_names}")

    return log, killed, loot
