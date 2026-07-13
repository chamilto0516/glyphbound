from __future__ import annotations

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Input, RichLog
from textual.reactive import reactive

import logging
import random
import re

from .combat import apply_spell_to_monster, apply_spell_aoe, execute_thrown_attack, execute_ranged_weapon_attack
from .combat_screen import (
    PotionSelectScreen,
    ScrollSelectScreen,
    RangedOptionsScreen,
    RangedOption,
)
from .dungeon import DOOR_CLOSED, SHOP, STAIR_DOWN, generate_dungeon
from .shop_screen import ShopScreen
from .items import EquipSlot, Item, ItemKind, HEAVY_WEAPONS, HEAVY_ARMOR, UNIQUE_HEAVY_WEAPONS
from .player import slot_label as _slot_label
from .map_view import MapView


def _item_label(item: "Item | None", *, lit: bool = False) -> str:
    """Display name for an equipped item. Torches show '(lit)' while equipped."""
    if item is None:
        return "—"
    if lit and item.name == "Torch":
        return "Torch (lit)"
    return item.name


def _ammo_line(player: "Player") -> str:
    """Stats-panel line listing nonzero ammo counts, or '' if the player carries none."""
    parts = [f"{ammo_type.title()}s {count}" for ammo_type, count in player.ammo.items() if count > 0]
    if not parts:
        return ""
    return f"[dim]Ammo:[/dim] {' · '.join(parts)}"
from .player import CharacterClass, Player
from .spells import Spell, SpellEffect
from .targeting import PendingRangedAction, TargetingSession, TargetShape
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

    #death-log-header {
        color: #888888;
        margin-top: 1;
    }

    .death-log-line {
        color: #cc4444;
    }
    """

    def __init__(self, player: "Player", floor: int, last_msgs: list = None) -> None:
        super().__init__()
        self.player    = player
        self.floor     = floor
        self.last_msgs = last_msgs or []

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
            if self.last_msgs:
                yield Static("  Last messages:", id="death-log-header")
                for line in self.last_msgs:
                    yield Static(f"  {line}", classes="death-log-line")
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

        max_hp_total = p.max_hp + p.max_hp_bonus
        hp_color = "bold bright_red" if p.hp <= max_hp_total * 0.25 else "bold bright_white"
        lines = [
            f"[bold yellow]{p.name}[/bold yellow] the {p.char_class.value}",
            f"Lv {p.level}   Floor {self.floor_num}   [yellow]{p.gold}gp[/yellow]",
            f"HP: [{hp_color}]{p.hp:>3}[/{hp_color}]/{max_hp_display:<3}  Atk/Def: {p.attack}/{p.defense}" + (f"  DR: {p.damage_reduction}" if p.damage_reduction else ""),
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
        ammo_line = _ammo_line(p)
        if ammo_line:
            lines.append(ammo_line)
        lines.append("[dim]────────────────────────[/dim]")
        # equipped slots
        weapon    = p.equipped.get(EquipSlot.WEAPON.value)
        helmet    = p.equipped.get(EquipSlot.HELMET.value)
        armor     = p.equipped.get(EquipSlot.ARMOR.value)
        shield    = p.equipped.get(EquipSlot.SHIELD.value)
        ring_l    = p.equipped.get(EquipSlot.RING_LEFT.value)
        ring_r    = p.equipped.get(EquipSlot.RING_RIGHT.value)
        amulet    = p.equipped.get(EquipSlot.AMULET.value)
        boots     = p.equipped.get(EquipSlot.BOOTS.value)
        gloves    = p.equipped.get(EquipSlot.GLOVES.value)
        off_label = "2H" if p.is_dual_wielding else "S"
        lines.append(f"[dim]W:[/dim]{_item_label(weapon):<14} [dim]H:[/dim]{_item_label(helmet)}")
        lines.append(f"[dim]A:[/dim]{_item_label(armor):<14} [dim]{off_label}:[/dim]{_item_label(shield, lit=True)}")
        lines.append(f"[dim]RL:[/dim]{_item_label(ring_l):<13} [dim]RR:[/dim]{_item_label(ring_r)}")
        lines.append(f"[dim]N:[/dim]{_item_label(amulet):<14} [dim]B:[/dim]{_item_label(boots)}")
        if gloves:
            lines.append(f"[dim]G:[/dim]{gloves.name}")
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
        self._history: list[str] = []

    def add(self, msg: str) -> None:
        self.write(msg)
        self._history.append(_strip_markup(msg))
        self._logger.info(_strip_markup(msg))

    def last_lines(self, n: int = 5) -> list[str]:
        return self._history[-n:]


# ── Inventory screen ──────────────────────────────────────────────────────────

class InventoryScreen(Screen):
    CSS = """
    InventoryScreen {
        background: black;
        align: center middle;
    }

    #inv-box {
        width: 66;
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

    #inv-hint {
        color: #888888;
        margin-bottom: 1;
    }

    #inv-equipped-header {
        color: ansi_bright_green;
        text-style: bold;
        margin-top: 1;
    }

    #inv-bag-header {
        color: ansi_bright_cyan;
        text-style: bold;
        margin-top: 1;
    }

    #inv-equipped {
        height: auto;
        max-height: 12;
        overflow-y: auto;
    }

    #inv-bag {
        height: auto;
        max-height: 12;
        overflow-y: auto;
    }

    #inv-actions {
        color: #aaaaaa;
        margin-top: 1;
    }

    #inv-msg {
        color: ansi_bright_cyan;
        margin-top: 0;
        height: 1;
    }
    """

    # Canonical slot display order for the Equipped section
    _SLOT_ORDER = [
        "weapon", "shield", "armor", "helmet",
        "ring_left", "ring_right", "amulet", "boots", "gloves",
    ]

    def __init__(self, player: Player) -> None:
        super().__init__()
        self.player = player
        self._selected: int = 0
        self._last_msg: str | None = None

    def _flat_items(self) -> list[tuple[Item, bool, str]]:
        """
        Returns (item, is_equipped, slot_key) for every item, equipped slots
        first (in canonical order), then bag items.
        """
        result = []
        for slot in self._SLOT_ORDER:
            item = self.player.equipped.get(slot)
            if item is not None:
                result.append((item, True, slot))
        for item in self.player.inventory:
            result.append((item, False, ""))
        return result

    def compose(self) -> ComposeResult:
        with Static(id="inv-box"):
            yield Static("Equipment & Inventory", id="inv-title")
            yield Static(
                "[dim]↑↓/jk[/dim] navigate   "
                "[bold](E)[/bold]quip/Remove   "
                "[bold](U)[/bold]se   "
                "[bold](D)[/bold]rop   "
                "[dim]Esc[/dim] close",
                id="inv-hint",
            )
            yield Static("── Equipped ─────────────────────────────────────", id="inv-equipped-header")
            yield Static(id="inv-equipped")
            yield Static("── Pack ──────────────────────────────────────────", id="inv-bag-header")
            yield Static(id="inv-bag")
            yield Static("", id="inv-actions")
            yield Static("", id="inv-msg")

    def on_mount(self) -> None:
        self._selected = 0
        self._refresh_list()

    def _refresh_list(self) -> None:
        items = self._flat_items()
        if items:
            self._selected = max(0, min(self._selected, len(items) - 1))

        equipped_widget = self.query_one("#inv-equipped", Static)
        bag_widget      = self.query_one("#inv-bag",      Static)
        actions_widget  = self.query_one("#inv-actions",  Static)

        # Split into two groups
        equipped_items = [(it, sl) for it, eq, sl in items if eq]
        bag_items      = [(it, sl) for it, eq, sl in items if not eq]

        # ── Equipped section ──────────────────────────────────────────────────
        if equipped_items:
            eq_lines = []
            for idx, (it, sl) in enumerate(equipped_items):
                flat_idx = idx
                display = _item_label(it, lit=(sl == EquipSlot.SHIELD.value))
                label = f"[bold green]{_slot_label(sl):>10}[/bold green]  {display}"
                if flat_idx == self._selected:
                    eq_lines.append(f"[bold ansi_bright_yellow]> {label}[/bold ansi_bright_yellow]")
                else:
                    eq_lines.append(f"  {label}")
            equipped_widget.update("\n".join(eq_lines))
        else:
            equipped_widget.update("  [dim](nothing equipped)[/dim]")

        # ── Bag section ───────────────────────────────────────────────────────
        eq_count = len(equipped_items)
        if bag_items:
            bag_lines = []
            for idx, (it, _sl) in enumerate(bag_items):
                flat_idx = eq_count + idx
                if flat_idx == self._selected:
                    bag_lines.append(f"[bold ansi_bright_yellow]> {it}[/bold ansi_bright_yellow]")
                else:
                    bag_lines.append(f"  {it}")
            bag_widget.update("\n".join(bag_lines))
        else:
            bag_widget.update("  [dim](empty)[/dim]")

        # ── Action hints for selected item ────────────────────────────────────
        if not items:
            actions_widget.update("")
            return
        item, is_eq, slot = items[self._selected]
        opts = []
        if is_eq:
            opts.append("[bold](E)[/bold]remove")
        elif item.equip_slot:
            opts.append("[bold](E)[/bold]quip")
        if item.kind == ItemKind.POTION:
            opts.append("[bold](U)[/bold]se")
        if item.kind == ItemKind.SCROLL:
            opts.append("[bold](U)[/bold]se scroll")
        opts.append("[bold](D)[/bold]rop")
        actions_widget.update("  ".join(opts))

    def on_key(self, event) -> None:
        items = self._flat_items()

        if event.key == "escape":
            self.dismiss(self._last_msg)
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

        item, is_eq, slot = items[self._selected]
        msg = None

        if event.key == "e":
            if is_eq:
                msg = self.player.unequip(EquipSlot(slot))
            elif item.equip_slot:
                msg, _ = self.player.equip(item)
        elif event.key == "u":
            if item.kind == ItemKind.POTION:
                msg = self.player.use_potion(item)
            elif item.kind == ItemKind.SCROLL:
                msg, _ = self.player.use_scroll(item)
        elif event.key == "d":
            msg, _ = self.player.drop(item)
            self._selected = max(0, self._selected - 1)

        if msg:
            self._last_msg = msg
            self.query_one("#inv-msg", Static).update(f"[dim]{msg}[/dim]")
            self._refresh_list()


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
        width: 38;
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

    #action-bar {
        width: 100%;
        height: 4;
        background: #111111;
        color: white;
        padding: 0 1;
        border: round #6e6e6e;
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
        ("r", "rage",            "Rage"),
        ("e", "envenom",         "Envenom"),
        ("p", "potion",          "Potion"),
        ("c", "scroll",          "Scroll"),
        ("f", "flee",            "Flee"),
        ("x", "disarm_trap",     "Disarm trap"),
        ("t", "ranged",          "Ranged attack"),
        ("k", "scroll_log_up",   "Scroll log up"),
        ("j", "scroll_log_down", "Scroll log down"),
        ("pageup",   "scroll_log_up",   "Scroll log up"),
        ("pagedown", "scroll_log_down", "Scroll log down"),
        ("q", "quit",            "Quit"),
    ]

    FLEE_FREEZE_TURNS = 3   # turns engaged monsters are stunned after a successful flee

    TORCH_BURNOUT_DAMAGE = 30   # damage in one combat past which a torch may gutter out
    TORCH_BURNOUT_CHANCE = 0.50

    def __init__(self, reveal_all: bool = False) -> None:
        super().__init__()
        self.reveal_all = reveal_all   # --light debug flag
        self._combat_damage_taken = 0  # damage accumulated in the current engagement
        self._torch_at_risk = True     # re-armed each combat; one burnout roll per combat
        self._targeting: TargetingSession | None = None

    def compose(self) -> ComposeResult:
        self.dungeon = generate_dungeon(floor=1, place_up_stair=False)
        self.player: Player | None = None
        self.map_view = MapView(self.dungeon, reveal_all=self.reveal_all)
        self.stats_panel = StatsPanel()
        self.message_log = MessageLog()

        yield Static("Glyphbound", id="title-bar")
        yield self.map_view
        with Static(id="bottom-bar"):
            yield self.stats_panel
            yield self.message_log
        action_bar = Static("", id="action-bar")
        action_bar.border_title = "Commands"
        yield action_bar

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
        self.map_view.refresh()
        self._refresh_action_bar()

    def _update_title(self) -> None:
        title = self.query_one("#title-bar", Static)
        title.update(f"Glyphbound — {self.dungeon.theme.name}  [Floor {self.dungeon.floor}]")
        title.styles.color = self.dungeon.theme.title_color

    def action_move_up(self)    -> None: self._move_or_aim(0, -1)
    def action_move_down(self)  -> None: self._move_or_aim(0,  1)
    def action_move_left(self)  -> None: self._move_or_aim(-1, 0)
    def action_move_right(self) -> None: self._move_or_aim(1,  0)

    def _move_or_aim(self, dx: int, dy: int) -> None:
        if self._targeting is not None:
            self._aim_cursor(dx, dy)
            return
        self._move(dx, dy)

    def action_scroll_log_up(self) -> None:
        if len(self.screen_stack) == 1:
            self.message_log.scroll_up()

    def action_scroll_log_down(self) -> None:
        if len(self.screen_stack) == 1:
            self.message_log.scroll_down()

    def _move(self, dx: int, dy: int) -> None:
        if not self.player:
            return

        # Check if status effects prevent movement
        from .status_effects import can_move
        move_allowed, move_msgs = can_move(self.player)
        if not move_allowed:
            for msg in move_msgs:
                self.message_log.add(msg)
            self._resolve_turn()  # turn consumed — lets the block itself tick down
            return

        nx, ny = self.dungeon.party_x + dx, self.dungeon.party_y + dy
        monster = self.dungeon.monster_at(nx, ny)
        if monster:
            self._bump_attack(monster, nx, ny)
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
        elif tile == SHOP:
            self._enter_shop()
        else:
            # Check for trap trigger on landing tile
            trap = self.dungeon.trap_at(x, y)
            if trap:
                self._trigger_trap(x, y, trap)
                if self.player.hp == 0:
                    return
            # Auto-pick-up anything on the landing tile
            items = list(self.dungeon.items_at(x, y))
            for item in items:
                msg = self.player.pick_up(item)
                self.dungeon.remove_item(x, y, item)
                self.message_log.add(msg)
                self._check_pickup_levelup()
            # The world takes its turn (monsters act, buffs decay, death checked)
            self._resolve_turn()

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
        self.message_log.add(msg)

        # Apply status effect if trap has one
        if trap.applies_effect:
            from .status_effects import apply_effect, StatusEffect
            effect_type, duration, potency = trap.applies_effect
            effect = StatusEffect(
                effect_type=effect_type,
                duration=duration,
                potency=potency,
                source=trap.name
            )
            effect_msg = apply_effect(self.player, effect)
            if effect_msg:
                self.message_log.add(f"  {effect_msg}")

        self.dungeon.remove_trap(x, y)
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

    # ── Turn-based combat (map-level) ────────────────────────────────────────

    def _bump_attack(self, monster, mx: int, my: int) -> None:
        """Player walks into a monster: one player strike, then the world takes a turn."""
        from .combat import execute_player_attack
        from .status_effects import can_attack

        # Check if status effects prevent attacking
        attack_allowed, attack_msgs = can_attack(self.player)
        if not attack_allowed:
            for msg in attack_msgs:
                self.message_log.add(msg)
            self._resolve_turn()  # turn consumed
            return

        for line in execute_player_attack(self.player, monster):
            self.message_log.add(line)

        if monster.hp == 0:
            self._reward_kill(monster, mx, my)
            self.stats_panel.refresh()
            self.map_view.refresh()
            self._resolve_turn()
            return

        # Monster survived — it (and every other monster) acts on the world turn.
        self._resolve_turn()

    def _reward_kill(self, monster, mx: int, my: int) -> None:
        """Grant XP, handle level-up, remove the monster, and drop loot on its tile."""
        self.player.xp += monster.xp_value
        self.player.stat_monsters_killed += 1
        self.message_log.add(f"You defeated the {monster.name}! +{monster.xp_value} XP")
        leveled, level_msgs = self.player.check_level_up()
        for line in level_msgs:
            self.message_log.add(line)
        self.dungeon.remove_monster(mx, my)
        loot = monster.drop_loot()
        for item in loot:
            self.dungeon.place_item(mx, my, item)
        if loot:
            self.message_log.add(f"  {monster.name} dropped: {', '.join(i.name for i in loot)}")

    def _check_pickup_levelup(self) -> None:
        """Log any level-up that resulted from XP gained via pickup or potion."""
        leveled, msgs = self.player.check_level_up()
        if leveled:
            for line in msgs:
                self.message_log.add(line)

    def _resolve_turn(self) -> None:
        """Advance the world one turn after a turn-consuming player action.

        Monsters act, combat buffs decay, the UI refreshes, and death is
        checked exactly once. Every player action that costs a turn (move,
        bump, rage, spell, potion, scroll) ends by calling this.
        """
        if not self.player or self.player.hp == 0:
            return
        self._monster_turns()

        # Tick player status effects (poison, burning DoT)
        from .status_effects import tick_effects
        effect_msgs = tick_effects(self.player)
        for msg in effect_msgs:
            self.message_log.add(msg)

        self.player.tick_buffs()
        self._decay_combat_buffs()
        self._check_torch_burnout()
        self.stats_panel.refresh()
        self.map_view.refresh()
        self._refresh_action_bar()
        if self.player.hp == 0:
            self._player_died()

    def _check_torch_burnout(self) -> None:
        """A torch may gutter out after the player takes heavy damage in a fight.

        Damage accumulates across the engagement; once it crosses the
        threshold a single chance is rolled. When combat ends the tally and
        the roll re-arm for the next fight.
        """
        if not self._in_combat():
            self._combat_damage_taken = 0
            self._torch_at_risk = True
            return
        if not self._torch_at_risk:
            return
        if self._combat_damage_taken <= self.TORCH_BURNOUT_DAMAGE:
            return
        self._torch_at_risk = False  # only one roll per combat
        torch = self.player.equipped.get(EquipSlot.SHIELD.value)
        if torch is None or torch.light_radius <= 0 or torch.name != "Torch":
            return
        if random.random() < self.TORCH_BURNOUT_CHANCE:
            del self.player.equipped[EquipSlot.SHIELD.value]
            self.message_log.add(
                "[bold yellow]Your torch sputters and dies in the chaos![/bold yellow]"
            )

    def _in_combat(self) -> bool:
        """True if any monster is within its chase range of the player (engaged)."""
        return bool(self._engaged_monsters())

    def _decay_combat_buffs(self) -> None:
        """Clear temporary spell buffs once the player is no longer in combat."""
        if not self._in_combat():
            self.player.temp_defense_bonus = 0
            self.player.temp_defense_turns = 0
            self.player.temp_attack_bonus = 0
            self.player.damage_absorb = 0

    def _monster_turns(self) -> None:
        """Execute one AI turn for each monster on the map."""
        from .ai import ai_turn
        from .status_effects import tick_effects, can_move

        # Snapshot positions to avoid mutating dict during iteration
        monster_positions = list(self.dungeon.monsters.items())

        for (mx, my), monster in monster_positions:
            # Monster may have been removed (e.g. killed) since the snapshot
            if self.dungeon.monster_at(mx, my) != monster:
                continue
            # A dead player ends the turn immediately — no piling on a corpse
            if self.player.hp == 0:
                return

            # Tick monster status effects (poison, burning DoT may kill)
            effect_msgs = tick_effects(monster)
            for msg in effect_msgs:
                self.message_log.add(msg)
            if monster.hp <= 0:
                self._reward_kill(monster, mx, my)
                continue

            # Check if status effects prevent action (stunned, bound)
            move_allowed, move_msgs = can_move(monster)
            for msg in move_msgs:
                self.message_log.add(msg)
            if not move_allowed:
                continue

            # Frozen monsters (e.g. after the player flees) lose their turn
            if monster.frozen_turns > 0:
                monster.frozen_turns -= 1
                continue

            # Boss special abilities (summon/AoE) pre-empt normal movement/melee
            if self._monster_special(monster, mx, my):
                continue

            new_pos = ai_turn(self.dungeon, monster, mx, my)
            if not new_pos:
                continue
            new_x, new_y = new_pos
            if (new_x, new_y) == (self.dungeon.party_x, self.dungeon.party_y):
                # Adjacent monster attacks instead of moving onto the player
                self._monster_attack(monster)
            else:
                self.dungeon.move_monster(mx, my, new_x, new_y)

    def _monster_attack(self, monster) -> None:
        """A single monster attacks the player. Logs only; death handled by caller."""
        from .combat import execute_monster_attack

        hp_before = self.player.hp
        for line in execute_monster_attack(self.player, monster):
            self.message_log.add(line)
        self._combat_damage_taken += max(0, hp_before - self.player.hp)

    def _monster_special(self, monster, mx: int, my: int) -> bool:
        """Boss ability engine: phase change, Summon, AoE. Returns True if the
        monster's turn was consumed by an ability (caller should skip normal
        move/melee); False means fall through to ai_turn as usual.
        """
        if not monster.is_boss:
            return False

        from .ai import manhattan_distance
        from .combat import execute_monster_aoe

        # Cooldowns tick down every world turn regardless of engagement.
        if monster.summon_cooldown > 0:
            monster.summon_cooldown -= 1
        if monster.aoe_cooldown > 0:
            monster.aoe_cooldown -= 1

        # Phase change: a one-time buff once HP drops to/below the threshold.
        if (monster.phase_threshold and not monster.phase_triggered
                and monster.hp <= monster.max_hp * monster.phase_threshold):
            monster.phase_triggered = True
            monster.attack = int(monster.attack * 1.3)
            monster.summon_cooldown = 0
            monster.aoe_cooldown = 0
            self.message_log.add(
                f"[bold magenta]{monster.name} shudders and enters a new phase![/bold magenta]"
            )

        px, py = self.dungeon.party_x, self.dungeon.party_y
        dist = manhattan_distance(mx, my, px, py)
        if dist > monster.chase_range:
            return False  # not engaged — abilities only fire once the fight is on

        if (monster.summon_spawner and monster.summon_cooldown == 0
                and (monster.summon_max == 0 or monster.summoned_so_far < monster.summon_max)):
            to_spawn = min(monster.summon_count, monster.summon_max - monster.summoned_so_far) \
                if monster.summon_max else monster.summon_count
            spawned = []
            for _ in range(max(0, to_spawn)):
                spot = self.dungeon.find_spawn_tile(mx, my, radius=3)
                if spot is None:
                    break
                sx, sy = spot
                add = monster.summon_spawner()
                add.spawn_x, add.spawn_y = sx, sy
                self.dungeon.place_monster(sx, sy, add)
                spawned.append(add.name)
                monster.summoned_so_far += 1
            if spawned:
                monster.summon_cooldown = monster.summon_cooldown_max
                self.message_log.add(
                    f"[bold]{monster.name} calls forth {', '.join(spawned)}![/bold]"
                )
                return True

        if monster.aoe_range and monster.aoe_cooldown == 0 and dist <= monster.aoe_range:
            hp_before = self.player.hp
            for line in execute_monster_aoe(self.player, monster):
                self.message_log.add(line)
            self._combat_damage_taken += max(0, hp_before - self.player.hp)
            monster.aoe_cooldown = monster.aoe_cooldown_max
            return True

        return False

    # ── Action bar ───────────────────────────────────────────────────────────

    def _refresh_action_bar(self) -> None:
        """Update the bottom action bar with the commands available right now."""
        bar = self.query_one("#action-bar", Static)
        p = self.player
        if p is None:
            bar.update("")
            return

        if self._targeting is not None:
            bar.update(
                "[bold]WASD[/bold] aim   [bold]Tab[/bold] cycle target   "
                "[bold]Enter[/bold] fire   [bold]Esc[/bold] cancel"
            )
            return

        engaged = self._in_combat()
        parts: list[str] = []

        # Movement / basic attack is always available
        parts.append("[bold]WASD[/bold] move" + ("/attack" if engaged else ""))

        # Rage — Warriors only
        if p.char_class == CharacterClass.WARRIOR:
            if p.rage_active:
                parts.append(f"[bold red](R)age:{p.rage_turns_remaining}[/bold red]")
            elif not p.rage_used_this_floor:
                parts.append("[bold](R)[/bold]age")
            else:
                parts.append("[dim](R)age used[/dim]")

        # Envenom — Thieves only
        if p.char_class == CharacterClass.THIEF:
            if p.envenom_charges > 0:
                parts.append(f"[bold yellow](E)nvenom:{p.envenom_charges}[/bold yellow]")
            elif not p.envenom_used_this_floor:
                parts.append("[bold](E)[/bold]nvenom")
            else:
                parts.append("[dim](E)nvenom used[/dim]")

        # Spells — casters with at least one affordable spell
        if p.spells:
            can_cast = any(s.mp_cost <= p.mp for s in p.spells)
            parts.append("[bold](Z)[/bold]Spell" if can_cast else "[dim](Z)Spell[/dim]")

        # Potions
        if any(i.kind == ItemKind.POTION for i in p.inventory):
            parts.append("[bold](P)[/bold]otion")

        # Scrolls
        if any(i.kind == ItemKind.SCROLL for i in p.inventory):
            parts.append("[bold](C)[/bold]Scroll")

        # Flee — only meaningful while engaged
        if engaged:
            parts.append("[bold](F)[/bold]lee")

        # Ranged — any affordable damage/turn-undead spell or a throwable item
        if self._ranged_options():
            parts.append("[bold](T)[/bold]arget")

        # Items on the floor
        if self.dungeon.items_at(self.dungeon.party_x, self.dungeon.party_y):
            parts.append("[bold](G)[/bold]et")

        parts.append("[bold](I)[/bold]nv")

        if p.invuln_active:
            parts.append(f"[bold cyan]INVULN:{p.invuln_turns_remaining}[/bold cyan]")
        if p.damage_absorb > 0:
            parts.append(f"[bold cyan]ABSORB:{p.damage_absorb}[/bold cyan]")
        if p.temp_defense_turns > 0:
            parts.append(f"[bold cyan]DEF+{p.temp_defense_bonus}({p.temp_defense_turns}t)[/bold cyan]")

        # Status effects
        from .status_effects import EffectType
        for etype, effect in p.status_effects.items():
            color = {
                EffectType.POISONED: "green",
                EffectType.STUNNED: "bright_yellow",
                EffectType.BURNING: "bright_red",
                EffectType.BOUND: "bright_magenta",
                EffectType.SILENCED: "dim",
            }.get(etype, "white")
            parts.append(f"[{color}]{etype.value.upper()}:{effect.duration}[/{color}]")

        # Second line: log scroll + quit hints, always present
        scroll_hint = "[dim](J/K) scroll log   (Q)uit[/dim]"

        bar.update("   ".join(parts) + "\n" + scroll_hint)

    def _player_died(self) -> None:
        self.message_log.add("── YOU HAVE DIED ──")
        last_msgs = self.message_log.last_lines(5)
        self.push_screen(
            DeathScreen(self.player, self.dungeon.floor, last_msgs),
            callback=self._death_dismissed,
        )

    def _death_dismissed(self, restart: bool) -> None:
        if restart:
            self.dungeon = generate_dungeon(floor=1, place_up_stair=False)
            self.player = None
            self.stats_panel.player = None
            self.map_view.dungeon = self.dungeon
            self.map_view.refresh()
            self._update_title()
            self.push_screen(ClassSelectScreen(), callback=self._class_chosen)

    def _can_act(self) -> bool:
        """True when the main map is active and a living player can take a turn.

        Guards app-level action bindings so they don't fire while a modal
        screen (inventory, spellbook, shop, …) is open — Textual app bindings
        otherwise bubble up underneath a pushed screen.
        """
        return (
            self.player is not None
            and self.player.hp > 0
            and len(self.screen_stack) == 1
            and self._targeting is None
        )

    def action_get_item(self) -> None:
        # Manual pickup fallback; items also auto-collect on move. No turn cost.
        if not self._can_act():
            return
        x, y = self.dungeon.party_x, self.dungeon.party_y
        items = list(self.dungeon.items_at(x, y))
        for item in items:
            msg = self.player.pick_up(item)
            self.dungeon.remove_item(x, y, item)
            self.message_log.add(msg)
            self._check_pickup_levelup()
        self.stats_panel.refresh()
        self.map_view.refresh()
        self._refresh_action_bar()

    def action_inventory(self) -> None:
        if not self._can_act():
            return
        self.push_screen(InventoryScreen(self.player), callback=self._inv_closed)

    def _inv_closed(self, msg: str | None) -> None:
        if msg:
            self.message_log.add(msg)
        self.stats_panel.refresh()
        self.map_view.refresh()
        self._refresh_action_bar()

    # ── Map-level combat actions (each consumes a turn) ──────────────────────

    def action_rage(self) -> None:
        if not self._can_act():
            return
        if self.player.char_class != CharacterClass.WARRIOR:
            return
        if self.player.rage_used_this_floor:
            self.message_log.add("You have already raged this floor.")
            return
        self.message_log.add(self.player.activate_rage())
        self._resolve_turn()

    def action_envenom(self) -> None:
        if not self._can_act():
            return
        if self.player.char_class != CharacterClass.THIEF:
            return
        if self.player.envenom_used_this_floor:
            self.message_log.add("You have already used Envenom this floor.")
            return
        self.player.envenom_charges = 3
        self.player.envenom_used_this_floor = True
        self.message_log.add("[bold yellow]You coat your blade with poison. Next 3 hits will envenom your foes![/bold yellow]")
        self._resolve_turn()

    def action_spells(self) -> None:
        if not self._can_act():
            return
        if not self.player.spells:
            self.message_log.add("Your class cannot cast spells.")
            return

        # Check if status effects prevent spell casting
        from .status_effects import can_cast
        cast_allowed, cast_msgs = can_cast(self.player)
        if not cast_allowed:
            for msg in cast_msgs:
                self.message_log.add(msg)
            return

        self.push_screen(SpellScreen(self.player), callback=self._spell_chosen)

    def _spell_chosen(self, spell: Spell | None) -> None:
        if spell is None:
            return  # cancelled — no turn consumed

        if spell.effect in (SpellEffect.DAMAGE, SpellEffect.TURN_UNDEAD):
            action = PendingRangedAction(kind="spell", spell=spell, label=spell.name)
            if spell.target_shape == TargetShape.SELF:
                self._resolve_self_aoe_spell(action)
            else:
                self._begin_targeting(
                    action,
                    spell.target_shape,
                    spell.spell_range,
                    spell.aoe_radius,
                )
            return  # turn cost (if any) is deferred to targeting confirm / self-AOE resolve

        msg, sentinel = self.player.cast_spell(spell)
        self.message_log.add(msg)
        if sentinel == -1:
            self._detect_magic_traps()
        elif sentinel == -2:
            self.dungeon.ambient_light_radius = max(
                self.dungeon.ambient_light_radius, spell.light_radius
            )

        self._resolve_turn()

    # ── Ranged targeting ──────────────────────────────────────────────────────

    def action_ranged(self) -> None:
        if not self._can_act():
            return
        options = self._ranged_options()
        if not options:
            self.message_log.add("You have no ranged attacks available.")
            return
        if len(options) == 1:
            self._ranged_option_chosen(options[0])
        else:
            self.push_screen(RangedOptionsScreen(options), callback=self._ranged_option_chosen)

    def _ranged_options(self) -> list:
        options = []
        for spell in self.player.spells:
            if spell.effect not in (SpellEffect.DAMAGE, SpellEffect.TURN_UNDEAD):
                continue
            if self.player.mp < spell.mp_cost:
                continue
            options.append(RangedOption(
                label=f"{spell.name}  ({spell.mp_cost} MP)  {spell.damage_label()}",
                kind="spell",
                spell=spell,
            ))
        seen_items = set()
        candidates = list(self.player.inventory) + [
            self.player.equipped.get(EquipSlot.WEAPON.value),
            self.player.equipped.get(EquipSlot.SHIELD.value),
        ]
        for item in candidates:
            if item is not None and item.throwable and id(item) not in seen_items:
                seen_items.add(id(item))
                options.append(RangedOption(
                    label=f"Throw {item.name}",
                    kind="thrown_weapon",
                    item=item,
                ))
        seen_ranged = set()
        for ranged_weapon in (
            self.player.equipped.get(EquipSlot.WEAPON.value),
            self.player.equipped.get(EquipSlot.SHIELD.value),
        ):
            if ranged_weapon is None or not ranged_weapon.ranged or id(ranged_weapon) in seen_ranged:
                continue
            seen_ranged.add(id(ranged_weapon))
            if ranged_weapon.ammo_type is None:
                options.append(RangedOption(
                    label=f"Shoot {ranged_weapon.name}",
                    kind="ranged_weapon",
                    item=ranged_weapon,
                ))
            elif self.player.get_ammo(ranged_weapon.ammo_type) > 0:
                ammo_left = self.player.get_ammo(ranged_weapon.ammo_type)
                options.append(RangedOption(
                    label=f"Shoot {ranged_weapon.name}  ({ranged_weapon.ammo_type.title()}s: {ammo_left})",
                    kind="ranged_weapon",
                    item=ranged_weapon,
                ))
        return options

    def _ranged_option_chosen(self, option: "RangedOption | None") -> None:
        if option is None:
            return  # cancelled — no turn consumed
        if option.kind == "spell":
            spell = option.spell
            action = PendingRangedAction(kind="spell", spell=spell, label=spell.name)
            if spell.target_shape == TargetShape.SELF:
                self._resolve_self_aoe_spell(action)
            else:
                self._begin_targeting(action, spell.target_shape, spell.spell_range, spell.aoe_radius)
        elif option.kind == "thrown_weapon":
            item = option.item
            action = PendingRangedAction(kind="thrown_weapon", item=item, label=f"Throw {item.name}")
            self._begin_targeting(action, TargetShape.SINGLE, item.thrown_range or 5, 0)
        else:  # ranged_weapon
            item = option.item
            action = PendingRangedAction(kind="ranged_weapon", item=item, label=f"Shoot {item.name}")
            self._begin_targeting(action, TargetShape.SINGLE, item.ranged_range or 7, 0)

    def _begin_targeting(self, action: PendingRangedAction, shape: TargetShape,
                          max_range: int, aoe_radius: int) -> None:
        px, py = self.dungeon.party_x, self.dungeon.party_y
        monster_cycle = self.dungeon.visible_monsters(px, py, max_range or 0)
        if monster_cycle:
            cursor_x, cursor_y = monster_cycle[0][0]
            cycle_index = 0
        else:
            cursor_x, cursor_y = px, py
            cycle_index = -1
        session = TargetingSession(
            action=action,
            shape=shape,
            max_range=max_range or 0,
            aoe_radius=aoe_radius,
            cursor_x=cursor_x,
            cursor_y=cursor_y,
            monster_cycle=monster_cycle,
            cycle_index=cycle_index,
        )
        self._targeting = session
        self._push_targeting_overlay()
        self._refresh_action_bar()

    def _push_targeting_overlay(self) -> None:
        session = self._targeting
        if session is None:
            self.map_view.targeting_cursor = None
            self.map_view.targeting_aoe_radius = 0
            self.map_view.targeting_valid = True
        else:
            self.map_view.targeting_cursor = (session.cursor_x, session.cursor_y)
            self.map_view.targeting_aoe_radius = session.aoe_radius
            self.map_view.targeting_valid = self._targeting_is_valid(session)
        self.map_view.refresh()

    def _targeting_is_valid(self, session: TargetingSession) -> bool:
        if session.shape != TargetShape.SINGLE:
            return True
        return self.dungeon.monster_at(session.cursor_x, session.cursor_y) is not None

    def _aim_cursor(self, dx: int, dy: int) -> None:
        session = self._targeting
        if session is None:
            return
        px, py = self.dungeon.party_x, self.dungeon.party_y
        nx, ny = session.cursor_x + dx, session.cursor_y + dy
        if session.max_range and max(abs(nx - px), abs(ny - py)) > session.max_range:
            return
        if (nx, ny) not in self.dungeon.visible:
            return
        session.cursor_x, session.cursor_y = nx, ny
        session.cycle_index = -1
        self._push_targeting_overlay()

    def action_target_cycle(self) -> None:
        session = self._targeting
        if session is None or not session.monster_cycle:
            return
        session.cycle_index = (session.cycle_index + 1) % len(session.monster_cycle)
        pos, _ = session.monster_cycle[session.cycle_index]
        session.cursor_x, session.cursor_y = pos
        self._push_targeting_overlay()

    def on_key(self, event) -> None:
        if self._targeting is None:
            return
        if event.key == "escape":
            self._cancel_targeting()
            event.stop()
        elif event.key in ("enter", "space"):
            self._confirm_targeting()
            event.stop()
        elif event.key == "tab":
            # Textual's default Screen binding maps "tab" to focus-next, which
            # would otherwise steal this key before action_target_cycle fires.
            self.action_target_cycle()
            event.stop()
            event.prevent_default()

    def _cancel_targeting(self) -> None:
        self._targeting = None
        self._push_targeting_overlay()
        self._refresh_action_bar()

    def _confirm_targeting(self) -> None:
        session = self._targeting
        if session is None:
            return
        pos = (session.cursor_x, session.cursor_y)
        px, py = self.dungeon.party_x, self.dungeon.party_y
        if session.max_range and max(abs(pos[0] - px), abs(pos[1] - py)) > session.max_range:
            self.message_log.add("Out of range.")
            return  # stay in targeting — free retry
        if pos not in self.dungeon.visible:
            self.message_log.add("You can't see a target there.")
            return  # stay in targeting — free retry

        if session.shape == TargetShape.SINGLE:
            monster = self.dungeon.monster_at(*pos)
            self._resolve_single_target(session.action, pos, monster)
        else:  # POINT
            targets = self.dungeon.monsters_in_radius(pos[0], pos[1], session.aoe_radius)
            self._resolve_aoe(session.action, targets)

        self._targeting = None
        self._push_targeting_overlay()
        self._refresh_action_bar()
        self._resolve_turn()

    def _resolve_single_target(self, action: PendingRangedAction, pos, monster) -> None:
        if action.kind == "spell":
            spell = action.spell
            if monster is None:
                # Confirmed shot at an empty tile — still spends MP (per the
                # "whiff costs a turn+resource" rule), no monster to check/kill.
                msg, _ = self.player.cast_spell(spell)
                self.message_log.add(msg)
                self.message_log.add("  The spell finds no target.")
                return
            log, killed, loot = apply_spell_to_monster(self.player, spell, monster)
            for line in log:
                self.message_log.add(line)
            if killed:
                self.dungeon.remove_monster(*pos)
                for item in loot:
                    self.dungeon.place_item(*pos, item)
        elif action.kind == "thrown_weapon":
            item = action.item
            if item in self.player.inventory:
                self.player.inventory.remove(item)
            else:
                for slot, equipped_item in list(self.player.equipped.items()):
                    if equipped_item is item:
                        del self.player.equipped[slot]
                        break
            if monster is None:
                self.message_log.add(f"Your {item.name} clatters to the floor, hitting nothing.")
                self.dungeon.place_item(*pos, item)
                return
            log, killed = execute_thrown_attack(self.player, item, monster)
            for line in log:
                self.message_log.add(line)
            if killed:
                self._reward_kill(monster, *pos)
            else:
                self.dungeon.place_item(*pos, item)
        else:  # ranged_weapon
            weapon = action.item
            if weapon.ammo_type is not None:
                self.player.spend_ammo(weapon.ammo_type)
            if monster is None:
                self.message_log.add(f"Your {weapon.name} shot flies past, hitting nothing.")
                return
            log, killed = execute_ranged_weapon_attack(self.player, weapon, monster)
            for line in log:
                self.message_log.add(line)
            if killed:
                self._reward_kill(monster, *pos)

    def _resolve_aoe(self, action: PendingRangedAction, targets) -> None:
        spell = action.spell
        log, killed, loot = apply_spell_aoe(self.player, spell, targets)
        for line in log:
            self.message_log.add(line)
        for pos, _monster in killed:
            self.dungeon.remove_monster(*pos)
        for pos, item in loot:
            self.dungeon.place_item(*pos, item)

    def _resolve_self_aoe_spell(self, action: PendingRangedAction) -> None:
        spell = action.spell
        if self.player.mp < spell.mp_cost:
            self.message_log.add(f"Not enough MP to cast {spell.name}. (need {spell.mp_cost})")
            return  # no turn cost — spell never went off
        px, py = self.dungeon.party_x, self.dungeon.party_y
        targets = self.dungeon.monsters_in_radius(px, py, spell.aoe_radius)
        self._resolve_aoe(action, targets)
        self._resolve_turn()

    def action_potion(self) -> None:
        if not self._can_act():
            return
        if not any(i.kind == ItemKind.POTION for i in self.player.inventory):
            self.message_log.add("You have no potions.")
            return
        self.push_screen(PotionSelectScreen(self.player), callback=self._potion_chosen)

    def _potion_chosen(self, item: Item | None) -> None:
        if item is None:
            return  # cancelled — no turn consumed
        self.message_log.add(self.player.use_potion(item))
        self._check_pickup_levelup()
        self._resolve_turn()

    def action_scroll(self) -> None:
        if not self._can_act():
            return
        if not any(i.kind == ItemKind.SCROLL for i in self.player.inventory):
            self.message_log.add("You have no scrolls.")
            return
        self.push_screen(ScrollSelectScreen(self.player), callback=self._scroll_chosen)

    def _scroll_chosen(self, item: Item | None) -> None:
        if item is None:
            return  # cancelled — no turn consumed
        scroll_light = item.light_radius
        msg, fireball_dmg = self.player.use_scroll(item)
        self.message_log.add(msg)
        if scroll_light:
            self.dungeon.ambient_light_radius = max(
                self.dungeon.ambient_light_radius, scroll_light
            )
        if fireball_dmg:
            nearest = self.dungeon.nearest_monster()
            if nearest is not None:
                pos, monster = nearest
                monster.hp = max(0, monster.hp - fireball_dmg)
                self.message_log.add(
                    f"  {monster.name} takes {fireball_dmg} fire damage! "
                    f"HP: {monster.hp}/{monster.max_hp}"
                )
                if monster.hp == 0:
                    self._reward_kill(monster, *pos)
        self._resolve_turn()

    def action_flee(self) -> None:
        if not self._can_act():
            return
        engaged = self._engaged_monsters()
        if not engaged:
            self.message_log.add("There is nothing to flee from.")
            return
        # Thief: 50% + 5%/level (cap 100%). Others: a flat 25%.
        if self.player.char_class == CharacterClass.THIEF:
            chance = min(0.50 + self.player.level * 0.05, 1.0)
        else:
            chance = 0.25
        if random.random() < chance:
            for monster in engaged:
                monster.frozen_turns = self.FLEE_FREEZE_TURNS
            self.message_log.add(
                f"[bold green]You break away![/bold green] Your pursuers falter "
                f"for {self.FLEE_FREEZE_TURNS} turns — run!"
            )
            # Freeze takes hold this turn; monsters don't act on the way out.
            self._decay_combat_buffs()
            self.stats_panel.refresh()
            self.map_view.refresh()
            self._refresh_action_bar()
        else:
            self.message_log.add("[yellow]You fail to break away![/yellow]")
            self._resolve_turn()

    def _engaged_monsters(self) -> list:
        """Return every monster currently within its chase range of the player."""
        px, py = self.dungeon.party_x, self.dungeon.party_y
        return [
            monster
            for (mx, my), monster in self.dungeon.monsters.items()
            if abs(mx - px) + abs(my - py) <= monster.chase_range
        ]

    def action_quit(self) -> None:
        """Show quit confirmation dialog."""
        self.push_screen(QuitConfirmScreen(), callback=self._quit_confirmed)

    def _quit_confirmed(self, confirmed: bool) -> None:
        """Handle quit confirmation result."""
        if confirmed:
            self.exit()

    def _descend(self) -> None:
        next_floor = self.dungeon.floor + 1
        if self.player:
            self.player.stat_floors_descended += 1
            self.player.rage_used_this_floor = False
            self.player.rage_turns_remaining = 0
            self.player.envenom_used_this_floor = False
            self.player.envenom_charges = 0
            from .status_effects import remove_all_effects
            remove_all_effects(self.player)
        # Stairs crumble behind you — each floor is a fresh dungeon, no return.
        self.dungeon = generate_dungeon(floor=next_floor, place_up_stair=False)
        self.map_view.dungeon = self.dungeon
        self.map_view.refresh()
        self._update_title()
        self.stats_panel.floor_num = self.dungeon.floor
        self.stats_panel.refresh()
        self._refresh_action_bar()
        if self.player:
            self.message_log.add(
                "[dim]The stairs crumble to dust behind you.[/dim]"
            )
            self.message_log.add(
                f"Floor {self.dungeon.floor} — entering the {self.dungeon.theme.name}."
            )
            boss = self.dungeon.boss
            if boss is not None:
                title = f" — {boss.boss_title}" if boss.boss_title else ""
                self.message_log.add(
                    f"[bold red]{boss.name}{title} guards the way down.[/bold red]"
                )

    def _enter_shop(self) -> None:
        self.message_log.add("[bold yellow]You step into the merchant's stall.[/bold yellow]")
        self.push_screen(ShopScreen(self.player, self.dungeon.floor), callback=self._shop_closed)

    def _shop_closed(self, _result) -> None:
        self.stats_panel.refresh()
        self.map_view.refresh()
        self._refresh_action_bar()
