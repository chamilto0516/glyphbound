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


def _mitigate(player: Player, dmg: int) -> Tuple[int, str]:
    """Apply armor damage-reduction then the absorb pool to an incoming hit.

    A landed hit always deals at least 1 damage, so no amount of DR or absorb
    grants hard invulnerability. Returns (final_damage, log_note).
    """
    notes = ""
    dr = player.damage_reduction
    if dr:
        reduced = min(dmg, dr)
        dmg -= reduced
        if reduced:
            notes += f" [dim](-{reduced} armor)[/dim]"
    if player.damage_absorb > 0 and dmg > 0:
        absorbed = min(dmg, player.damage_absorb)
        player.damage_absorb -= absorbed
        dmg -= absorbed
        notes += f" [dim](absorbed {absorbed}, {player.damage_absorb} left)[/dim]"
    return max(1, dmg), notes


def _best_damage_spell(player: Player) -> Optional[Spell]:
    """Return the highest expected-damage spell the player can currently afford."""
    candidates = [
        s for s in player.spells
        if s.effect == SpellEffect.DAMAGE and player.mp >= s.mp_cost
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda s: s.damage_sides * s.damage_count)


def _attacker_hits(natural: int, attack: int, defense: int) -> bool:
    """Resolve a 1d10 hit. Natural 1 always misses, natural 10 always hits.

    These natural rules inherently cap hit chance at 10%–90% on a d10, so no
    high-DEF (or low-DEF) build can ever be fully immune or auto-hit.
    """
    if natural == 1:
        return False
    if natural == 10:
        return True
    return natural + attack > defense


def _single_weapon_attack(
    player: Player,
    monster: Monster,
    weapon: "Item | None",
    label: str,
    log: List[str],
) -> None:
    """Roll one weapon strike. Mutates monster.hp and appends to log."""
    from .player import CharacterClass
    from .status_effects import apply_effect, StatusEffect, EffectType
    p_natural = random.randint(1, 10)
    if not _attacker_hits(p_natural, player.attack, monster.defense):
        log.append(f"  Your {label} misses the {monster.name}.")
        return
    dmg = roll_damage(weapon)
    weapon_backstab = weapon.backstab_bonus if weapon else 0.0
    backstab = (
        player.char_class == CharacterClass.THIEF
        and random.random() < player.level * 0.10 + weapon_backstab
    )
    # Anti-undead weapons add extra radiant damage on top of the (possibly
    # multiplied) strike — the bonus itself is not doubled by backstab/rage.
    undead_bonus = 0
    if weapon and weapon.undead_bonus_sides and monster.is_undead:
        undead_bonus = sum(
            random.randint(1, weapon.undead_bonus_sides)
            for _ in range(weapon.undead_bonus_count)
        )
    if backstab:
        dmg *= 2
        dmg += undead_bonus
        monster.hp = max(0, monster.hp - dmg)
        smite = f" [bold bright_yellow](+{undead_bonus} radiant)[/bold bright_yellow]" if undead_bonus else ""
        log.append(f"  [bold yellow]BACKSTAB![/bold yellow] Your {label} strikes a vital spot for {dmg}!{smite} {monster.name} HP: {monster.hp}/{monster.max_hp}")
    elif player.rage_active:
        dmg *= 2
        dmg += undead_bonus
        player.rage_turns_remaining -= 1
        rage_note = " (Rage fades)" if player.rage_turns_remaining == 0 else f" (Rage: {player.rage_turns_remaining} left)"
        monster.hp = max(0, monster.hp - dmg)
        smite = f" [bold bright_yellow](+{undead_bonus} radiant)[/bold bright_yellow]" if undead_bonus else ""
        log.append(f"  [bold red]RAGE![/bold red] Your {label} smashes for {dmg}!{rage_note}{smite} {monster.name} HP: {monster.hp}/{monster.max_hp}")
    else:
        dmg += undead_bonus
        monster.hp = max(0, monster.hp - dmg)
        smite = f" [bold bright_yellow](+{undead_bonus} radiant)[/bold bright_yellow]" if undead_bonus else ""
        log.append(f"  Your {label} hits for {dmg}!{smite} {monster.name} HP: {monster.hp}/{monster.max_hp}")

    # Thief Envenom: apply poison if charges remain
    if player.char_class == CharacterClass.THIEF and player.envenom_charges > 0 and monster.hp > 0:
        player.envenom_charges -= 1
        effect = StatusEffect(
            effect_type=EffectType.POISONED,
            duration=3,
            potency=1,
            source="envenomed blade"
        )
        effect_msg = apply_effect(monster, effect)
        if effect_msg:
            log.append(f"  {effect_msg}")
        if player.envenom_charges == 0:
            log.append("  [dim](Envenom charges exhausted)[/dim]")


def execute_player_attack(player: Player, monster: Monster) -> List[str]:
    """Execute one player attack round. Dual-wielding Warriors strike twice. Returns log lines."""
    from .player import CharacterClass
    from .status_effects import can_cast
    log: List[str] = []
    player_weapon = player.equipped.get(EquipSlot.WEAPON.value)
    spell = _best_damage_spell(player) if player.char_class == CharacterClass.WIZARD else None

    # Wizard auto-cast: check if silenced
    cast_allowed = True
    if spell:
        cast_allowed, _ = can_cast(player)

    if spell and cast_allowed:
        msg, dmg = player.cast_spell(spell)
        monster.hp = max(0, monster.hp - dmg)
        log.append(f"  {msg}  {monster.name} HP: {monster.hp}/{monster.max_hp}")
    elif player.is_dual_wielding:
        wpn_name = player_weapon.name if player_weapon else "fists"
        off_wpn = player.off_hand_weapon
        off_name = off_wpn.name if off_wpn else "fists"
        _single_weapon_attack(player, monster, player_weapon, wpn_name, log)
        if monster.hp > 0:
            _single_weapon_attack(player, monster, off_wpn, off_name, log)
    else:
        wpn_name = player_weapon.name if player_weapon else "fists"
        strikes = player_weapon.strikes if player_weapon else 1
        for _ in range(strikes):
            if monster.hp == 0:
                break
            _single_weapon_attack(player, monster, player_weapon, wpn_name, log)
    return log


def execute_monster_attack(player: Player, monster: Monster) -> List[str]:
    """Execute one monster attack round. Mutates player.hp. Returns log lines."""
    from .player import CharacterClass
    from .status_effects import apply_effect, StatusEffect
    log: List[str] = []
    # Invulnerability blocks all damage; decrement counter
    if player.invuln_active:
        player.invuln_turns_remaining -= 1
        fade = " [dim](Invulnerability fades)[/dim]" if not player.invuln_active else ""
        log.append(f"  {monster.name} attacks — but you are invulnerable!{fade}")
        return log
    m_natural = random.randint(1, 10)
    if _attacker_hits(m_natural, monster.attack, player.defense):
        dmg = roll_damage(monster.weapon)
        # Warrior Toughness: 50% chance to absorb 1 point of damage
        if player.char_class == CharacterClass.WARRIOR and dmg > 1 and random.random() < 0.50:
            dmg -= 1
            toughness_note = " [dim](Toughness)[/dim]"
        else:
            toughness_note = ""
        dmg, notes = _mitigate(player, dmg)
        player.hp = max(0, player.hp - dmg)
        player.stat_damage_taken += dmg
        wpn_name = monster.weapon.name if monster.weapon else "claws"
        log.append(f"  {monster.name} hits you with {wpn_name} for {dmg}!{toughness_note}{notes} Your HP: {player.hp}/{player.max_hp}")

        # Apply on-hit status effect if configured
        if monster.on_hit_effect and random.random() < monster.on_hit_chance:
            effect = StatusEffect(
                effect_type=monster.on_hit_effect,
                duration=monster.on_hit_duration,
                potency=monster.on_hit_potency,
                source=f"{monster.name} attack"
            )
            effect_msg = apply_effect(player, effect)
            if effect_msg:
                log.append(f"  {effect_msg}")
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
    player.temp_defense_turns = 0
    player.temp_attack_bonus = 0
    player.damage_absorb = 0
    player.invuln_turns_remaining = 0

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


def apply_spell_aoe(
    player: Player,
    spell: Spell,
    targets: List[Tuple[Tuple[int, int], Monster]],
) -> Tuple[List[str], List[Tuple[Tuple[int, int], Monster]], List[Tuple[Tuple[int, int], Item]]]:
    """
    Apply one AOE (DAMAGE-effect) spell cast to every (pos, monster) pair in `targets`.
    MP is deducted and the cast message logged exactly once via player.cast_spell(spell);
    each target then takes an INDEPENDENT damage roll (not a shared pool split N ways).
    An empty `targets` list still spends MP — the player chose to cast at that point.
    Returns (log_lines, killed[(pos, monster)], loot[(pos, item)]).
    Caller removes killed monsters from the dungeon and places dropped loot.
    """
    log: List[str] = []
    killed: List[Tuple[Tuple[int, int], Monster]] = []
    loot: List[Tuple[Tuple[int, int], Item]] = []

    msg, _ = player.cast_spell(spell)
    log.append(msg)

    if not targets:
        log.append("  The blast catches nothing.")
        return log, killed, loot

    any_kill = False
    for pos, monster in targets:
        dmg = sum(random.randint(1, spell.damage_sides) for _ in range(spell.damage_count))
        monster.hp = max(0, monster.hp - dmg)
        log.append(f"  {monster.name} is caught in the blast for {dmg}! HP: {monster.hp}/{monster.max_hp}")
        if monster.hp == 0:
            player.xp += monster.xp_value
            player.stat_monsters_killed += 1
            log.append(f"  {monster.name} is slain! +{monster.xp_value} XP")
            drops = monster.drop_loot()
            if drops:
                loot_names = ", ".join(item.name for item in drops)
                log.append(f"  {monster.name} dropped: {loot_names}")
            for item in drops:
                loot.append((pos, item))
            killed.append((pos, monster))
            any_kill = True

    if any_kill:
        leveled, level_msgs = player.check_level_up()
        if leveled:
            log.extend(level_msgs)

    return log, killed, loot


def execute_thrown_attack(player: Player, item: Item, monster: Monster) -> Tuple[List[str], bool]:
    """
    A single thrown-weapon attack against a non-adjacent monster. Rolls to-hit like
    melee (thrown weapons are physical, unlike auto-hit spells) via _attacker_hits,
    and reuses roll_damage(item) for the damage die. Mutates monster.hp in place.
    Returns (log_lines, killed). Does not grant XP/loot — caller handles that via
    the existing _reward_kill helper, mirroring how execute_player_attack works.
    """
    log: List[str] = []
    natural = random.randint(1, 10)
    if not _attacker_hits(natural, player.attack, monster.defense):
        log.append(f"  Your thrown {item.name} sails past the {monster.name}!")
        return log, False
    dmg = roll_damage(item)
    monster.hp = max(0, monster.hp - dmg)
    log.append(f"  Your thrown {item.name} hits for {dmg}! {monster.name} HP: {monster.hp}/{monster.max_hp}")
    return log, monster.hp == 0


def execute_ranged_weapon_attack(player: Player, weapon: Item, monster: Monster) -> Tuple[List[str], bool]:
    """
    A single shot from a persistent ranged weapon (bow/sling/crossbow/wand) against a
    non-adjacent monster. Same to-hit/damage resolution as execute_thrown_attack, but the
    weapon itself is never removed — only the caller's ammo bookkeeping (if any) changes.
    Returns (log_lines, killed).
    """
    log: List[str] = []
    natural = random.randint(1, 10)
    if not _attacker_hits(natural, player.attack, monster.defense):
        log.append(f"  Your {weapon.name} shot sails past the {monster.name}!")
        return log, False
    dmg = roll_damage(weapon)
    undead_bonus = 0
    if weapon.undead_bonus_sides and monster.is_undead:
        undead_bonus = sum(
            random.randint(1, weapon.undead_bonus_sides)
            for _ in range(weapon.undead_bonus_count)
        )
    dmg += undead_bonus
    monster.hp = max(0, monster.hp - dmg)
    smite = f" [bold bright_yellow](+{undead_bonus} radiant)[/bold bright_yellow]" if undead_bonus else ""
    log.append(f"  Your {weapon.name} hits for {dmg}!{smite} {monster.name} HP: {monster.hp}/{monster.max_hp}")
    return log, monster.hp == 0
