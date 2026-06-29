from __future__ import annotations

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Input, RichLog
from textual.reactive import reactive

import logging
import random
import re

from .combat import apply_spell_to_monster
from .combat_screen import CombatResult, CombatScreen
from .dungeon import DOOR_CLOSED, STAIR_DOWN, STAIR_UP, generate_dungeon
from .items import EquipSlot, Item, ItemKind, HEAVY_WEAPONS, HEAVY_ARMOR, UNIQUE_HEAVY_WEAPONS
from .map_view import MapView
from .player import CharacterClass, Player
from .spells import Spell, SpellEffect
from .traps import Trap


# ── Class-select screen ────────────────────────────────────────────────────────

_CLASS_KEYS = {
    "w": CharacterClass.WARRIOR,
    "z": CharacterClass.WIZARD,
    "t": CharacterClass.THIEF,
    "c": CharacterClass.CLERIC,
}

_CLASS_DESCRIPTIONS = {
    CharacterClass.WARRIOR: "Can use any weapon, shield, or armor. No spells.",
    CharacterClass.WIZARD:  "Dagger/staff only, robes only. Casts spells; MP refills as you move.",
    CharacterClass.THIEF:   "Light armor, ranged weapons. Detects traps, picks locks. Scrolls only.",
    CharacterClass.CLERIC:  "Light armor, blunt weapons. Spells and turning; strong vs undead.",
}


class ClassSelectScreen(Screen):
    CSS = """
    ClassSelectScreen {
        background: black;
        align: center middle;
    }

    #select-box {
        width: 68;
        height: auto;
        border: double ansi_bright_yellow;
        padding: 1 2;
        background: black;
    }

    #select-title {
        text-align: center;
        text-style: bold;
        color: ansi_bright_yellow;
        margin-bottom: 1;
    }

    #select-hint {
        text-align: center;
        color: #888888;
    }

    .class-line {
        color: white;
        margin-bottom: 0;
    }
    """

    def compose(self) -> ComposeResult:
        with Static(id="select-box"):
            yield Static("Choose Your Class", id="select-title")
            yield Static("Press the highlighted key to select.", id="select-hint")
            yield Static("", classes="class-line")
            yield Static("[bold ansi_bright_yellow]W[/bold ansi_bright_yellow] — [bold]Warrior[/bold]  Any weapon or armor. No spells.       HP 20  ATK 6  DEF 4",       classes="class-line")
            yield Static("[bold ansi_bright_yellow]Z[/bold ansi_bright_yellow] — [bold]Wizard[/bold]   Dagger/staff, robes only. Casts spells. HP 10  ATK 2  DEF 1  MP 20", classes="class-line")
            yield Static("[bold ansi_bright_yellow]T[/bold ansi_bright_yellow] — [bold]Thief[/bold]    Light armor, ranged expert. Picks locks. HP 14  ATK 4  DEF 2",       classes="class-line")
            yield Static("[bold ansi_bright_yellow]C[/bold ansi_bright_yellow] — [bold]Cleric[/bold]   Light armor, blunt weapons. Turns undead. HP 16  ATK 3  DEF 3  MP 15", classes="class-line")

    def on_key(self, event) -> None:
        char_class = _CLASS_KEYS.get(event.key)
        if char_class:
            self.dismiss(char_class)


# ── Quit confirmation screen ───────────────────────────────────────────────────

class DeathScreen(Screen):
    CSS = """
    DeathScreen {
        background: rgba(0,0,0,0.92);
        align: center middle;
    }

    #death-box {
        width: 56;
        height: auto;
        border: double ansi_bright_red;
        padding: 1 2;
        background: black;
    }

    #death-title {
        text-align: center;
        text-style: bold;
        color: ansi_bright_red;
        margin-bottom: 0;
    }

    #death-subtitle {
        text-align: center;
        color: #888888;
        margin-bottom: 1;
    }

    #death-sep {
        color: #333333;
        margin-bottom: 1;
    }

    .stat-row {
        color: white;
    }

    #death-hint {
        text-align: center;
        color: #555555;
        margin-top: 1;
    }
    """

    def __init__(self, player: "Player", floor: int) -> None:
        super().__init__()
        self.player = player
        self.floor  = floor

    def compose(self) -> ComposeResult:
        p = self.player
        with Static(id="death-box"):
            yield Static("✝  YOU HAVE DIED  ✝", id="death-title")
            yield Static(
                f"{p.name} the {p.char_class.value}  —  slain on floor {self.floor}",
                id="death-subtitle",
            )
            yield Static("[dim]────────────────────────────────────────────────────[/dim]", id="death-sep")
            yield Static(f"  Level reached      {p.level}",                           classes="stat-row")
            yield Static(f"  XP earned          {p.xp}",                              classes="stat-row")
            yield Static(f"  Gold collected     {p.stat_gold_collected} gp",          classes="stat-row")
            yield Static(f"  Floors descended   {p.stat_floors_descended}",           classes="stat-row")
            yield Static(f"  Squares traveled   {p.stat_squares_traveled:,}",         classes="stat-row")
            yield Static(f"  Monsters defeated  {p.stat_monsters_killed}",            classes="stat-row")
            yield Static(f"  Damage taken       {p.stat_damage_taken}",               classes="stat-row")
            yield Static(f"  Items found        {p.stat_items_found}",                classes="stat-row")
            yield Static(f"  MP spent           {p.stat_mp_spent}",                   classes="stat-row")
            yield Static("[dim]────────────────────────────────────────────────────[/dim]", id="death-sep2")
            yield Static("Press Q to quit  or  R to restart", id="death-hint")

    def on_key(self, event) -> None:
        if event.key == "q":
            self.app.exit()
        elif event.key == "r":
            self.dismiss(True)


class QuitConfirmScreen(Screen):
    CSS = """
    QuitConfirmScreen {
        background: rgba(0,0,0,0.85);
        align: center middle;
    }

    #quit-box {
        width: 50;
        height: auto;
        border: double ansi_bright_red;
        padding: 1 2;
        background: black;
    }

    #quit-title {
        text-align: center;
        text-style: bold;
        color: ansi_bright_red;
        margin-bottom: 1;
    }

    #quit-hint {
        text-align: center;
        color: white;
        margin-bottom: 1;
    }

    #quit-actions {
        text-align: center;
        color: #aaaaaa;
    }
    """

    def compose(self) -> ComposeResult:
        with Static(id="quit-box"):
            yield Static("Quit Game?", id="quit-title")
            yield Static("Are you sure you want to exit?", id="quit-hint")
            yield Static("[bold]Y[/bold]es  /  [bold]N[/bold]o (or Esc)", id="quit-actions")

    def on_key(self, event) -> None:
        if event.key in ("y", "Y"):
            self.dismiss(True)
        elif event.key in ("n", "N", "escape"):
            self.dismiss(False)


# ── Name-entry screen ──────────────────────────────────────────────────────────

class NameEntryScreen(Screen):
    CSS = """
    NameEntryScreen {
        background: black;
        align: center middle;
    }

    #name-box {
        width: 50;
        height: auto;
        border: double ansi_bright_yellow;
        padding: 1 2;
        background: black;
    }

    #name-title {
        text-align: center;
        text-style: bold;
        color: ansi_bright_yellow;
        margin-bottom: 1;
    }

    #name-hint {
        color: white;
        margin-bottom: 1;
    }

    Input {
        background: black;
        border: solid #4d4d4d;
        color: white;
    }
    """

    def __init__(self, char_class: CharacterClass) -> None:
        super().__init__()
        self.char_class = char_class

    def compose(self) -> ComposeResult:
        with Static(id="name-box"):
            yield Static(f"Name Your {self.char_class.value}", id="name-title")
            yield Static("Enter a name (up to 20 characters) and press Enter:", id="name-hint")
            yield Input(placeholder="Name...", max_length=20, id="name-input")

    def on_mount(self) -> None:
        self.query_one("#name-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        name = event.value.strip()[:20] or self.char_class.value
        self.dismiss(name)


# ── Stats panel (bottom-left) ──────────────────────────────────────────────────

class StatsPanel(Static):
    player: reactive[Player | None] = reactive(None)
    floor_num: reactive[int] = reactive(1)

    def render(self) -> str:
        p = self.player
        if p is None:
            return ""
        xp_next = p.xp_to_next_level
        xp_display = f"{p.xp} (next: {xp_next})" if xp_next > 0 else f"{p.xp}"

        # Show max HP/MP with bonuses
        max_hp_display = f"{p.max_hp + p.max_hp_bonus}"
        max_mp_display = f"{p.max_mp + p.max_mp_bonus}"

        lines = [
            f"[bold yellow]{p.name}[/bold yellow] the {p.char_class.value}",
            f"Lv {p.level}   Floor {self.floor_num}   [yellow]{p.gold}gp[/yellow]",
            f"HP: [green]{p.hp:>3}[/green]/{max_hp_display:<3}  ATK:{p.attack:<3} DEF:{p.defense}",
            f"XP: {xp_display}",
        ]
        if p.has_mp:
            lines.append(f"MP: [cyan]{p.mp:>3}[/cyan]/{max_mp_display}")
        elif p.rage_active:
            lines.append(f"[bold red]RAGING — {p.rage_turns_remaining} turn(s) left[/bold red]")
        elif p.char_class == CharacterClass.WARRIOR and p.rage_used_this_floor:
            lines.append("[dim]Rage: used[/dim]")
        elif p.char_class == CharacterClass.WARRIOR:
            lines.append("[dim]Rage: ready[/dim]")
        else:
            lines.append("")
        lines.append("[dim]────────────────────────[/dim]")
        # equipped slots
        weapon = p.equipped.get(EquipSlot.WEAPON.value)
        helmet = p.equipped.get(EquipSlot.HELMET.value)
        armor  = p.equipped.get(EquipSlot.ARMOR.value)
        shield = p.equipped.get(EquipSlot.SHIELD.value)
        ring   = p.equipped.get(EquipSlot.RING.value)
        amulet = p.equipped.get(EquipSlot.AMULET.value)
        lines.append(f"[dim]W:[/dim]{weapon.name if weapon else '—':<14} [dim]H:[/dim]{helmet.name if helmet else '—'}")
        lines.append(f"[dim]A:[/dim]{armor.name  if armor  else '—':<14} [dim]S:[/dim]{shield.name if shield else '—'}")
        if ring or amulet:
            lines.append(f"[dim]R:[/dim]{ring.name if ring else '—':<14} [dim]N:[/dim]{amulet.name if amulet else '—'}")
        return "\n".join(lines)


# ── Message log (bottom-right) ─────────────────────────────────────────────────

_MARKUP_RE = re.compile(r"\[/?[^\]]*\]")


def _strip_markup(text: str) -> str:
    """Remove Rich markup tags so the file log stores clean plaintext."""
    return _MARKUP_RE.sub("", text)


class MessageLog(RichLog):
    _logger = logging.getLogger("glyphbound.messagelog")

    def __init__(self) -> None:
        super().__init__(max_lines=100, markup=True, auto_scroll=True)

    def add(self, msg: str) -> None:
        self.write(msg)
        self._logger.info(_strip_markup(msg))


# ── Inventory screen ──────────────────────────────────────────────────────────

class InventoryScreen(Screen):
    CSS = """
    InventoryScreen {
        background: black;
        align: center middle;
    }

    #inv-box {
        width: 60;
        height: auto;
        max-height: 90vh;
        border: double ansi_bright_yellow;
        padding: 1 2;
        background: black;
    }

    #inv-title {
        text-align: center;
        text-style: bold;
        color: ansi_bright_yellow;
        margin-bottom: 0;
    }

    #inv-count {
        text-align: center;
        color: #555555;
        margin-bottom: 1;
    }

    #inv-hint {
        color: #888888;
        margin-bottom: 1;
    }

    #inv-list {
        height: auto;
        max-height: 24;
        overflow-y: auto;
    }

    .inv-line {
        color: white;
    }

    #inv-actions {
        color: #aaaaaa;
        margin-top: 1;
    }
    """

    def __init__(self, player: Player) -> None:
        super().__init__()
        self.player = player
        self._selected: int = 0

    def _all_items(self) -> list[tuple[Item, bool, str]]:
        """Returns list of (item, is_equipped, slot_label)."""
        result = []
        for item in self.player.inventory:
            result.append((item, False, ""))
        for slot, item in self.player.equipped.items():
            result.append((item, True, slot))
        return result

    def compose(self) -> ComposeResult:
        with Static(id="inv-box"):
            yield Static("Inventory", id="inv-title")
            yield Static("", id="inv-count")
            yield Static(
                "[dim]↑↓[/dim] navigate   "
                "[bold](E)[/bold]quip/Unequip   "
                "[bold](U)[/bold]se   "
                "[bold](D)[/bold]rop   "
                "[bold](I)[/bold] close",
                id="inv-hint",
            )
            yield Static(id="inv-list")
            yield Static("", id="inv-actions")

    def on_mount(self) -> None:
        items = self._all_items()
        if items:
            self._selected = 0
        self._refresh_list()

    def _refresh_list(self) -> None:
        items = self._all_items()

        # Clamp selection
        if items:
            self._selected = max(0, min(self._selected, len(items) - 1))

        count_widget   = self.query_one("#inv-count",   Static)
        inv_list       = self.query_one("#inv-list",    Static)
        actions_widget = self.query_one("#inv-actions", Static)

        count_widget.update(f"[dim]{len(items)} item{'s' if len(items) != 1 else ''}[/dim]")

        if not items:
            inv_list.update("[dim](empty)[/dim]")
            actions_widget.update("")
            return

        lines = []
        for i, (item, equipped, slot) in enumerate(items):
            slot_tag = f" [dim][{slot}][/dim]" if equipped else ""
            if i == self._selected:
                lines.append(
                    f"[bold ansi_bright_yellow]>[/bold ansi_bright_yellow] "
                    f"[bold ansi_bright_yellow]{item}{slot_tag}[/bold ansi_bright_yellow]"
                )
            else:
                lines.append(f"  {item}{slot_tag}")
        inv_list.update("\n".join(lines))

        item, equipped, slot = items[self._selected]
        opts = []
        if item.equip_slot and not equipped:
            opts.append("[bold](E)[/bold]quip")
        if equipped:
            opts.append("[bold](E)[/bold]unequip")
        if item.kind == ItemKind.POTION:
            opts.append("[bold](U)[/bold]se")
        opts.append("[bold](D)[/bold]rop")
        actions_widget.update("  ".join(opts))

    def on_key(self, event) -> None:
        items = self._all_items()

        if event.key in ("escape", "i"):
            self.dismiss(None)
            return

        if not items:
            return

        if event.key in ("up", "k"):
            self._selected = (self._selected - 1) % len(items)
            self._refresh_list()
            return

        if event.key in ("down", "j"):
            self._selected = (self._selected + 1) % len(items)
            self._refresh_list()
            return

        item, equipped, slot = items[self._selected]
        msg = None

        if event.key == "e":
            if equipped:
                msg = self.player.unequip(EquipSlot(slot))
            elif item.equip_slot:
                msg, _ = self.player.equip(item)
        elif event.key == "u" and item.kind == ItemKind.POTION:
            msg = self.player.use_potion(item)
        elif event.key == "d":
            msg, _ = self.player.drop(item)
            self._selected = max(0, self._selected - 1)

        if msg:
            self.dismiss(msg)


# ── Spell screen ──────────────────────────────────────────────────────────────

class SpellScreen(Screen):
    CSS = """
    SpellScreen {
        background: black;
        align: center middle;
    }

    #spell-box {
        width: 56;
        height: auto;
        border: double ansi_bright_cyan;
        padding: 1 2;
        background: black;
    }

    #spell-title {
        text-align: center;
        text-style: bold;
        color: ansi_bright_cyan;
        margin-bottom: 1;
    }

    #spell-mp {
        color: #aaaaaa;
        margin-bottom: 1;
    }

    .spell-line {
        color: white;
    }

    #spell-hint {
        color: #888888;
        margin-top: 1;
    }
    """

    def __init__(self, player: Player) -> None:
        super().__init__()
        self.player = player

    def compose(self) -> ComposeResult:
        with Static(id="spell-box"):
            yield Static("Spellbook", id="spell-title")
            yield Static(f"MP: {self.player.mp} / {self.player.max_mp}", id="spell-mp")
            for i, spell in enumerate(self.player.spells):
                cost_color = "ansi_bright_cyan" if self.player.mp >= spell.mp_cost else "red"
                line = (
                    f"[bold]{i+1}.[/bold]  {spell.name}"
                    f"  [{cost_color}]{spell.mp_cost} MP[/{cost_color}]"
                    f"  [dim]{spell.damage_label()}[/dim]"
                    f"  [dim italic]{spell.description}[/dim italic]"
                )
                yield Static(line, classes="spell-line")
            yield Static("Press number to cast. Esc to cancel.", id="spell-hint")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
            return
        if event.character and event.character.isdigit():
            idx = int(event.character) - 1
            if 0 <= idx < len(self.player.spells):
                self.dismiss(self.player.spells[idx])


# ── Main app ───────────────────────────────────────────────────────────────────

class GlyphboundApp(App):
    CSS = """
    Screen {
        background: black;
        layout: vertical;
    }

    #title-bar {
        width: 100%;
        height: 1;
        background: black;
        content-align: center middle;
        color: white;
        text-style: bold;
    }

    MapView {
        width: 100%;
        height: 1fr;
        background: black;
    }

    #bottom-bar {
        width: 100%;
        height: 8;
        background: black;
        layout: horizontal;
        border-top: solid #4d4d4d;
    }

    StatsPanel {
        width: 28;
        height: 8;
        background: black;
        padding: 0 1;
        border-right: solid #4d4d4d;
        color: white;
    }

    MessageLog {
        width: 1fr;
        height: 8;
        background: black;
        padding: 0 1;
        color: white;
    }
    """

    BINDINGS = [
        ("w", "move_up",         "Move up"),
        ("s", "move_down",       "Move down"),
        ("a", "move_left",       "Move left"),
        ("d", "move_right",      "Move right"),
        ("g", "get_item",        "Get item"),
        ("i", "inventory",       "Inventory"),
        ("z", "spells",          "Spells"),
        ("x", "disarm_trap",     "Disarm trap"),
        ("pageup",   "scroll_log_up",   "Scroll log up"),
        ("pagedown", "scroll_log_down", "Scroll log down"),
        ("q", "quit",            "Quit"),
    ]

    def compose(self) -> ComposeResult:
        self.dungeon = generate_dungeon(floor=1, place_up_stair=False)
        self._floor_stack: list = []
        self.player: Player | None = None
        self.map_view = MapView(self.dungeon)
        self.stats_panel = StatsPanel()
        self.message_log = MessageLog()

        yield Static("Glyphbound", id="title-bar")
        yield self.map_view
        with Static(id="bottom-bar"):
            yield self.stats_panel
            yield self.message_log

    def on_mount(self) -> None:
        self._update_title()
        self.push_screen(ClassSelectScreen(), callback=self._class_chosen)

    def _class_chosen(self, char_class: CharacterClass) -> None:
        self._pending_class = char_class
        self.push_screen(NameEntryScreen(char_class), callback=self._name_chosen)

    def _name_chosen(self, name: str) -> None:
        char_class = self._pending_class
        self.player = Player(name=name, char_class=char_class)
        self.stats_panel.player = self.player
        self.stats_panel.floor_num = self.dungeon.floor
        self.message_log.add(
            f"{name} the {char_class.value} descends into the {self.dungeon.theme.name}."
        )
        self.stats_panel.refresh()

    def _update_title(self) -> None:
        title = self.query_one("#title-bar", Static)
        title.update(f"Glyphbound — {self.dungeon.theme.name}  [Floor {self.dungeon.floor}]")
        title.styles.color = self.dungeon.theme.title_color

    def action_move_up(self)    -> None: self._move(0, -1)
    def action_move_down(self)  -> None: self._move(0,  1)
    def action_move_left(self)  -> None: self._move(-1, 0)
    def action_move_right(self) -> None: self._move(1,  0)

    def action_scroll_log_up(self)   -> None: self.message_log.scroll_up()
    def action_scroll_log_down(self) -> None: self.message_log.scroll_down()

    def _move(self, dx: int, dy: int) -> None:
        if not self.player:
            return
        nx, ny = self.dungeon.party_x + dx, self.dungeon.party_y + dy
        monster = self.dungeon.monster_at(nx, ny)
        if monster:
            self.push_screen(
                CombatScreen(self.player, monster, (nx, ny)),
                callback=self._combat_finished,
            )
            return

        # Check if player is about to open a door (tile at dest is DOOR_CLOSED)
        dest_tile = self.dungeon.tile_at(nx, ny)
        opening_door = dest_tile == DOOR_CLOSED

        moved = self.dungeon.move_party(dx, dy)
        if not moved:
            return  # blocked by wall

        self.player.on_move()
        self.stats_panel.refresh()
        x, y = self.dungeon.party_x, self.dungeon.party_y

        # Thief door-open trap detection scan
        if opening_door and self.player.char_class == CharacterClass.THIEF:
            self._thief_detect_traps()

        tile = self.dungeon.tile_at(x, y)
        if tile == STAIR_DOWN:
            self._descend()
        elif tile == STAIR_UP:
            self._ascend()
        else:
            # Check for trap trigger on landing tile
            trap = self.dungeon.trap_at(x, y)
            if trap:
                self._trigger_trap(x, y, trap)
                if self.player.hp == 0:
                    return
            # After player moves, run monster AI turns
            self._monster_turns()
            self.map_view.refresh()
            items = self.dungeon.items_at(x, y)
            if items:
                names = ", ".join(i.name for i in items)
                if len(items) == 1:
                    self.message_log.add(f"You notice something interesting: {names}. (G to pick up)")
                else:
                    self.message_log.add(f"You notice several things of interest: {names}. (G to pick up)")

    def _detect_magic_traps(self) -> None:
        """Detect Magic reveals all Flame Ward traps on the current floor."""
        found = []
        for (tx, ty), trap in self.dungeon.traps.items():
            if trap.is_magic and not trap.is_detected:
                trap.is_detected = True
                found.append(trap.name)
        if found:
            self.message_log.add(
                f"[bold cyan]Detect Magic reveals {len(found)} magical trap(s) on this floor![/bold cyan]"
            )
            self.map_view.refresh()
        else:
            self.message_log.add("Detect Magic finds no magical traps here.")

    def _thief_detect_traps(self) -> None:
        """Thief scans for traps within 20 Manhattan distance when opening a door."""
        import random as _rng
        chance = self.player.trap_detect_chance
        if chance <= 0:
            return
        px, py = self.dungeon.party_x, self.dungeon.party_y
        found = []
        for (tx, ty), trap in self.dungeon.traps.items():
            if trap.is_detected:
                continue
            dist = abs(tx - px) + abs(ty - py)
            if dist <= 20 and _rng.random() < chance:
                trap.is_detected = True
                found.append(trap.name)
        if found:
            names = ", ".join(found)
            self.message_log.add(
                f"[bold red]Your thief senses tingle — you detect: {names}![/bold red]"
            )
        else:
            self.message_log.add("You check for traps but find nothing.")

    def _trigger_trap(self, x: int, y: int, trap: Trap) -> None:
        """Player steps on a trap tile — deal damage and remove the trap."""
        dmg, msg = trap.trigger()
        self.player.hp = max(0, self.player.hp - dmg)
        self.player.stat_damage_taken += dmg
        self.dungeon.remove_trap(x, y)
        self.message_log.add(msg)
        self.stats_panel.refresh()
        self.map_view.refresh()
        if self.player.hp == 0:
            self._player_died()

    def action_disarm_trap(self) -> None:
        """Thief disarms a trap on current or adjacent tile."""
        if not self.player:
            return
        if self.player.char_class != CharacterClass.THIEF:
            self.message_log.add("Only a Thief can disarm traps.")
            return
        px, py = self.dungeon.party_x, self.dungeon.party_y
        # Look for a detected trap on current tile or orthogonal neighbors
        target_pos = None
        target_trap = None
        for dx, dy in ((0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)):
            trap = self.dungeon.trap_at(px + dx, py + dy)
            if trap and trap.is_detected:
                target_pos = (px + dx, py + dy)
                target_trap = trap
                break
        if target_trap is None:
            self.message_log.add("No detected trap nearby to disarm.")
            return
        import random as _rng
        if _rng.random() < self.player.trap_disarm_chance:
            self.dungeon.remove_trap(*target_pos)
            self.message_log.add(
                f"[bold green]You disarm the {target_trap.name}![/bold green]"
            )
            self.map_view.refresh()
        else:
            self.message_log.add(
                f"You fail to disarm the {target_trap.name}!"
            )

    def _monster_turns(self) -> None:
        """Execute AI turn for each monster on the map."""
        from .ai import ai_turn

        # Snapshot positions to avoid mutating dict during iteration
        monster_positions = list(self.dungeon.monsters.items())

        for (mx, my), monster in monster_positions:
            # Check monster still exists (might have been killed by another monster bumping player)
            if self.dungeon.monster_at(mx, my) != monster:
                continue

            new_pos = ai_turn(self.dungeon, monster, mx, my)
            if new_pos:
                new_x, new_y = new_pos
                # Check if monster is trying to bump player
                if (new_x, new_y) == (self.dungeon.party_x, self.dungeon.party_y):
                    # Monster attacks player
                    self._monster_attacks_player(monster, mx, my)
                    # Don't move the monster; it stays in place after attacking
                else:
                    # Normal movement
                    self.dungeon.move_monster(mx, my, new_x, new_y)

    def _monster_attacks_player(self, monster, mx: int, my: int) -> None:
        """Handle a monster attacking the player from (mx, my)."""
        from .combat import execute_monster_attack

        lines = execute_monster_attack(self.player, monster)
        for line in lines:
            self.message_log.add(line)

        self.stats_panel.refresh()

        if self.player.hp == 0:
            self._player_died()

    def _player_died(self) -> None:
        self.message_log.add("── YOU HAVE DIED ──")
        self.push_screen(
            DeathScreen(self.player, self.dungeon.floor),
            callback=self._death_dismissed,
        )

    def _death_dismissed(self, restart: bool) -> None:
        if restart:
            self.dungeon = generate_dungeon(floor=1, place_up_stair=False)
            self._floor_stack.clear()
            self.player = None
            self.stats_panel.player = None
            self.map_view.dungeon = self.dungeon
            self.map_view.refresh()
            self._update_title()
            self.push_screen(ClassSelectScreen(), callback=self._class_chosen)

    def _combat_finished(self, result: CombatResult) -> None:
        for line in result.log:
            self.message_log.add(line)
        if result.monster_killed:
            self.dungeon.remove_monster(*result.pos)
            # Place loot drops on the ground
            for item in result.loot:
                self.dungeon.place_item(*result.pos, item)
        self.stats_panel.refresh()
        self.map_view.refresh()
        if not result.survived and not result.fled:
            self._player_died()

    def action_get_item(self) -> None:
        if not self.player:
            return
        x, y = self.dungeon.party_x, self.dungeon.party_y
        items = list(self.dungeon.items_at(x, y))
        if not items:
            self.message_log.add("Nothing to pick up here.")
            return
        for item in items:
            msg = self.player.pick_up(item)
            self.dungeon.remove_item(x, y, item)
            self.message_log.add(msg)
        self.stats_panel.refresh()
        self.map_view.refresh()

    def action_inventory(self) -> None:
        if not self.player:
            return
        self.push_screen(InventoryScreen(self.player), callback=self._inv_closed)

    def _inv_closed(self, msg: str | None) -> None:
        if msg:
            self.message_log.add(msg)
        self.stats_panel.refresh()
        self.map_view.refresh()

    def action_spells(self) -> None:
        if not self.player:
            return
        if not self.player.spells:
            self.message_log.add("Your class cannot cast spells.")
            return
        self.push_screen(SpellScreen(self.player), callback=self._spell_chosen)

    def _spell_chosen(self, spell: Spell | None) -> None:
        if spell is None:
            return

        if spell.effect in (SpellEffect.DAMAGE, SpellEffect.TURN_UNDEAD):
            nearest = self.dungeon.nearest_monster()
            if nearest is None:
                self.message_log.add("No monsters in range.")
                return
            pos, monster = nearest
            log, killed, loot = apply_spell_to_monster(self.player, spell, monster)
            for line in log:
                self.message_log.add(line)
            if killed:
                self.dungeon.remove_monster(*pos)
                # Place loot drops on the ground
                for item in loot:
                    self.dungeon.place_item(*pos, item)
        else:
            msg, sentinel = self.player.cast_spell(spell)
            self.message_log.add(msg)
            if sentinel == -1:
                self._detect_magic_traps()

        self.stats_panel.refresh()
        self.map_view.refresh()

    def action_quit(self) -> None:
        """Show quit confirmation dialog."""
        self.push_screen(QuitConfirmScreen(), callback=self._quit_confirmed)

    def _quit_confirmed(self, confirmed: bool) -> None:
        """Handle quit confirmation result."""
        if confirmed:
            self.exit()

    def _descend(self) -> None:
        sx, sy = self.dungeon.stair_down_pos
        self._floor_stack.append((self.dungeon, sx, sy))
        next_floor = self.dungeon.floor + 1
        if self.player:
            self.player.stat_floors_descended += 1
            self.player.rage_used_this_floor = False
            self.player.rage_turns_remaining = 0
        self.dungeon = generate_dungeon(floor=next_floor, place_up_stair=True)
        self.map_view.dungeon = self.dungeon
        self.map_view.refresh()
        self._update_title()
        self.stats_panel.floor_num = self.dungeon.floor
        self.stats_panel.refresh()
        if self.player:
            self.message_log.add(
                f"Floor {self.dungeon.floor} — entering the {self.dungeon.theme.name}."
            )

    def _ascend(self) -> None:
        if not self._floor_stack:
            return
        prev_dungeon, stair_x, stair_y = self._floor_stack.pop()
        prev_dungeon.party_x, prev_dungeon.party_y = stair_x, stair_y
        self.dungeon = prev_dungeon
        if self.player:
            self.player.rage_used_this_floor = False
            self.player.rage_turns_remaining = 0
        self.map_view.dungeon = self.dungeon
        self.map_view.refresh()
        self._update_title()
        self.stats_panel.floor_num = self.dungeon.floor
        self.stats_panel.refresh()
        if self.player:
            self.message_log.add(
                f"Ascended to floor {self.dungeon.floor}."
            )
