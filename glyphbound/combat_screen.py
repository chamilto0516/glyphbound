from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

from .combat import (
    apply_spell_to_monster,
    execute_flee_attempt,
    execute_monster_attack,
    execute_player_attack,
)
from .items import EquipSlot, Item, ItemKind
from .monsters import Monster
from .player import Player
from .spells import Spell, SpellEffect


@dataclass
class CombatResult:
    survived: bool
    fled: bool
    monster_killed: bool
    pos: Tuple[int, int]
    log: List[str] = field(default_factory=list)
    loot: List[Item] = field(default_factory=list)


# ── Potion-select screen ──────────────────────────────────────────────────────

class PotionSelectScreen(Screen):
    CSS = """
    PotionSelectScreen {
        background: rgba(0,0,0,0.85);
        align: center middle;
    }

    #pot-box {
        width: 44;
        height: auto;
        border: double ansi_bright_yellow;
        padding: 1 2;
        background: black;
    }

    #pot-title {
        text-align: center;
        text-style: bold;
        color: ansi_bright_yellow;
        margin-bottom: 1;
    }

    #pot-hint {
        color: #888888;
        margin-top: 1;
    }

    .pot-line {
        color: white;
    }
    """

    def __init__(self, player: Player) -> None:
        super().__init__()
        self.player = player

    def _potions(self) -> List[Item]:
        return [i for i in self.player.inventory if i.kind == ItemKind.POTION]

    def compose(self) -> ComposeResult:
        potions = self._potions()
        with Static(id="pot-box"):
            yield Static("Use Potion", id="pot-title")
            if not potions:
                yield Static("[dim](no potions in inventory)[/dim]", classes="pot-line")
            else:
                for i, p in enumerate(potions):
                    yield Static(f"[bold]{i+1}.[/bold]  {p}", classes="pot-line")
            yield Static("Press number to drink. Esc to cancel.", id="pot-hint")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
            return
        potions = self._potions()
        if event.character and event.character.isdigit():
            idx = int(event.character) - 1
            if 0 <= idx < len(potions):
                self.dismiss(potions[idx])


# ── Weapon-select screen ───────────────────────────────────────────────────────

class WeaponSelectScreen(Screen):
    CSS = """
    WeaponSelectScreen {
        background: rgba(0,0,0,0.85);
        align: center middle;
    }

    #wpn-box {
        width: 44;
        height: auto;
        border: double ansi_bright_yellow;
        padding: 1 2;
        background: black;
    }

    #wpn-title {
        text-align: center;
        text-style: bold;
        color: ansi_bright_yellow;
        margin-bottom: 1;
    }

    #wpn-hint {
        color: #888888;
        margin-top: 1;
    }

    .wpn-line {
        color: white;
    }
    """

    def __init__(self, player: Player) -> None:
        super().__init__()
        self.player = player

    def _weapons(self) -> List[Item]:
        return [i for i in self.player.inventory if i.kind == ItemKind.WEAPON]

    def compose(self) -> ComposeResult:
        weapons = self._weapons()
        with Static(id="wpn-box"):
            yield Static("Switch Weapon", id="wpn-title")
            if not weapons:
                yield Static("[dim](no weapons in inventory)[/dim]", classes="wpn-line")
            else:
                for i, w in enumerate(weapons):
                    yield Static(f"[bold]{i+1}.[/bold]  {w}", classes="wpn-line")
            yield Static("Press number to equip. Esc to cancel.", id="wpn-hint")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
            return
        weapons = self._weapons()
        if event.character and event.character.isdigit():
            idx = int(event.character) - 1
            if 0 <= idx < len(weapons):
                self.dismiss(weapons[idx])


# ── Combat screen ──────────────────────────────────────────────────────────────

_HP_FULL  = "█"
_HP_EMPTY = "░"
_HP_BAR_WIDTH = 10


def _hp_bar(current: int, maximum: int) -> str:
    if maximum == 0:
        return _HP_EMPTY * _HP_BAR_WIDTH
    filled = round(_HP_BAR_WIDTH * current / maximum)
    ratio = current / maximum
    if ratio > 0.5:
        color = "green"
    elif ratio > 0.25:
        color = "yellow"
    else:
        color = "red"
    bar = f"[{color}]{_HP_FULL * filled}[/{color}]{_HP_EMPTY * (_HP_BAR_WIDTH - filled)}"
    return bar


class CombatScreen(Screen):
    CSS = """
    CombatScreen {
        background: rgba(0,0,0,0.85);
        align: center middle;
    }

    #combat-box {
        width: 58;
        height: auto;
        border: double ansi_bright_red;
        padding: 1 2;
        background: black;
    }

    #combat-title {
        text-align: center;
        text-style: bold;
        color: ansi_bright_red;
        margin-bottom: 1;
    }

    #monster-row {
        color: white;
        margin-bottom: 0;
    }

    #player-row {
        color: white;
        margin-bottom: 1;
    }

    #combat-sep {
        color: #4d4d4d;
        margin-bottom: 0;
    }

    #combat-log {
        color: white;
        height: 6;
        margin-bottom: 0;
    }

    #combat-sep2 {
        color: #4d4d4d;
        margin-bottom: 1;
    }

    #combat-actions {
        color: #aaaaaa;
    }
    """

    def __init__(self, player: Player, monster: Monster, pos: Tuple[int, int]) -> None:
        super().__init__()
        self.player = player
        self.monster = monster
        self.pos = pos
        self._combat_log: List[str] = []
        self._result_log: List[str] = []  # accumulated for CombatResult
        self._loot: List[Item] = []  # collected loot drops

    def compose(self) -> ComposeResult:
        with Static(id="combat-box"):
            yield Static("⚔  COMBAT", id="combat-title")
            yield Static("", id="monster-row")
            yield Static("", id="player-row")
            yield Static("[dim]──────────────────────────────────────────────────[/dim]", id="combat-sep")
            yield Static("", id="combat-log")
            yield Static("[dim]──────────────────────────────────────────────────[/dim]", id="combat-sep2")
            yield Static("", id="combat-actions")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        p, m = self.player, self.monster

        # Monster row
        self.query_one("#monster-row", Static).update(
            f"{m.name:<20} HP: {_hp_bar(m.hp, m.max_hp)}  {m.hp}/{m.max_hp}"
        )
        # Player row
        self.query_one("#player-row", Static).update(
            f"{p.name:<20} HP: {_hp_bar(p.hp, p.max_hp)}  {p.hp}/{p.max_hp}"
            + (f"   MP: {p.mp}/{p.max_mp}" if p.has_mp else "")
        )
        # Rolling log (last 6 lines)
        log_lines = self._combat_log[-6:]
        while len(log_lines) < 6:
            log_lines = [""] + log_lines
        self.query_one("#combat-log", Static).update("\n".join(log_lines))

        # Action bar
        weapon = p.equipped.get(EquipSlot.WEAPON.value)
        wpn_label = weapon.name if weapon else "fists"
        has_inv_weapons = any(i.kind == ItemKind.WEAPON for i in p.inventory)
        has_potions = any(i.kind == ItemKind.POTION for i in p.inventory)

        parts = [f"[bold](A)[/bold]ttack [{wpn_label}]"]
        if has_inv_weapons:
            parts.append("[bold](W)[/bold]eapon")
        if p.spells:
            can_cast = any(s.mp_cost <= p.mp for s in p.spells)
            spell_label = "[bold](Z)[/bold]Spell" if can_cast else "[dim](Z)Spell[/dim]"
            parts.append(spell_label)
        if has_potions:
            parts.append("[bold](P)[/bold]otion")
        parts.append("[bold](F)[/bold]lee")
        self.query_one("#combat-actions", Static).update("  ".join(parts))

    def _push_log(self, lines: List[str]) -> None:
        self._combat_log.extend(lines)
        self._result_log.extend(lines)

    def _end_combat(self, survived: bool, fled: bool, monster_killed: bool) -> None:
        # Clear temp buffs after combat
        self.player.temp_defense_bonus = 0
        self.player.temp_attack_bonus = 0
        result = CombatResult(
            survived=survived,
            fled=fled,
            monster_killed=monster_killed,
            pos=self.pos,
            log=list(self._result_log),
            loot=list(self._loot),
        )
        self.dismiss(result)

    def on_key(self, event) -> None:
        key = event.key
        if key == "a":
            self._do_attack()
        elif key == "w":
            self._do_weapon()
        elif key == "z":
            self._do_spell()
        elif key == "p":
            self._do_potion()
        elif key == "f":
            self._do_flee()
        else:
            return
        # Stop the event so it doesn't bubble to the App's global bindings
        # (a/w/z collide with move_left/move_up/spells), which would fire a
        # second action — e.g. opening a duplicate spellbook and double-casting.
        event.stop()
        event.prevent_default()

    # ── Combat actions ─────────────────────────────────────────────────────────

    def _do_attack(self) -> None:
        lines = execute_player_attack(self.player, self.monster)
        self._push_log(lines)

        if self.monster.hp == 0:
            self.player.xp += self.monster.xp_value
            self.player.stat_monsters_killed += 1
            self._push_log([f"You defeated the {self.monster.name}! +{self.monster.xp_value} XP"])
            leveled, level_msgs = self.player.check_level_up()
            if leveled:
                self._push_log(level_msgs)
            # Generate loot
            loot = self.monster.drop_loot()
            self._loot.extend(loot)
            if loot:
                loot_names = ", ".join(item.name for item in loot)
                self._push_log([f"  {self.monster.name} dropped: {loot_names}"])
            self._refresh()
            self._end_combat(survived=True, fled=False, monster_killed=True)
            return

        lines = execute_monster_attack(self.player, self.monster)
        self._push_log(lines)
        self._refresh()

        if self.player.hp == 0:
            self._push_log([f"You have been slain by the {self.monster.name}..."])
            self._end_combat(survived=False, fled=False, monster_killed=False)

    def _do_weapon(self) -> None:
        self.app.push_screen(WeaponSelectScreen(self.player), callback=self._weapon_chosen)

    def _weapon_chosen(self, item: Optional[Item]) -> None:
        if item is not None:
            msg, _ = self.player.equip(item)
            self._push_log([f"  {msg}"])
        self._refresh()

    def _do_spell(self) -> None:
        if not self.player.spells:
            return
        from .app import SpellScreen
        self.app.push_screen(SpellScreen(self.player), callback=self._spell_chosen)

    def _spell_chosen(self, spell: Optional[Spell]) -> None:
        if spell is None:
            self._refresh()
            return

        if spell.effect in (SpellEffect.DAMAGE, SpellEffect.TURN_UNDEAD):
            log, killed, loot = apply_spell_to_monster(self.player, spell, self.monster)
            self._push_log(log)
            if killed:
                self._push_log([f"You defeated the {self.monster.name}! +{self.monster.xp_value} XP"])
                leveled, level_msgs = self.player.check_level_up()
                if leveled:
                    self._push_log(level_msgs)
                # Collect loot
                self._loot.extend(loot)
                if loot:
                    loot_names = ", ".join(item.name for item in loot)
                    self._push_log([f"  {self.monster.name} dropped: {loot_names}"])
                self._refresh()
                self._end_combat(survived=True, fled=False, monster_killed=True)
                return
        else:
            msg, _ = self.player.cast_spell(spell)
            self._push_log([msg])

        # Monster counter-attacks after player spell
        if self.monster.hp > 0:
            lines = execute_monster_attack(self.player, self.monster)
            self._push_log(lines)

        self._refresh()

        if self.player.hp == 0:
            self._push_log([f"You have been slain by the {self.monster.name}..."])
            self._end_combat(survived=False, fled=False, monster_killed=False)

    def _do_potion(self) -> None:
        if not any(i.kind == ItemKind.POTION for i in self.player.inventory):
            return
        self.app.push_screen(PotionSelectScreen(self.player), callback=self._potion_chosen)

    def _potion_chosen(self, item: Optional[Item]) -> None:
        if item is None:
            self._refresh()
            return

        # Use the potion (doesn't consume turn, but monster attacks after)
        msg = self.player.use_potion(item)
        self._push_log([f"  {msg}"])

        # Monster counter-attacks after player uses potion
        if self.monster.hp > 0:
            lines = execute_monster_attack(self.player, self.monster)
            self._push_log(lines)

        self._refresh()

        if self.player.hp == 0:
            self._push_log([f"You have been slain by the {self.monster.name}..."])
            self._end_combat(survived=False, fled=False, monster_killed=False)

    def _do_flee(self) -> None:
        lines, succeeded = execute_flee_attempt(self.player, self.monster)
        self._push_log(lines)
        self._refresh()
        if succeeded:
            self._end_combat(survived=True, fled=True, monster_killed=False)
        elif self.player.hp == 0:
            self._end_combat(survived=False, fled=False, monster_killed=False)
