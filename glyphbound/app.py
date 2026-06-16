from __future__ import annotations

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Input
from textual.reactive import reactive

from .dungeon import STAIR_DOWN, STAIR_UP, generate_dungeon
from .map_view import MapView
from .player import CharacterClass, Player


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
        lines = [
            f"[bold yellow]{p.name}[/bold yellow] the {p.char_class.value}",
            f"Lv {p.level}   Floor {self.floor_num}",
            f"HP: [green]{p.hp:>3}[/green] / {p.max_hp:<3}",
            f"ATK: {p.attack:<3}  DEF: {p.defense:<3}",
            f"XP:  {p.xp}",
        ]
        if p.has_mp:
            lines.append(f"MP: [cyan]{p.mp:>3}[/cyan] / {p.max_mp:<3}")
        else:
            lines.append("")
        lines.append("[dim]──────────────────────[/dim]")
        lines.append("[bold]Inventory[/bold]")
        lines.append(" (empty)")
        return "\n".join(lines)


# ── Message log (bottom-right) ─────────────────────────────────────────────────

class MessageLog(Static):
    def __init__(self) -> None:
        super().__init__()
        self._messages: list[str] = []

    def add(self, msg: str) -> None:
        self._messages.append(msg)
        if len(self._messages) > 6:
            self._messages = self._messages[-6:]
        self.update("\n".join(self._messages))

    def clear(self) -> None:
        self._messages = []
        self.update("")


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
        ("w", "move_up",    "Move up"),
        ("s", "move_down",  "Move down"),
        ("a", "move_left",  "Move left"),
        ("d", "move_right", "Move right"),
        ("q", "quit",       "Quit"),
        ("escape", "quit",  "Quit"),
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

    def _move(self, dx: int, dy: int) -> None:
        self.dungeon.move_party(dx, dy)
        if self.player:
            self.player.on_move()
            self.stats_panel.player = self.player
            self.stats_panel.refresh()
        tile = self.dungeon.tile_at(self.dungeon.party_x, self.dungeon.party_y)
        if tile == STAIR_DOWN:
            self._descend()
        elif tile == STAIR_UP:
            self._ascend()
        else:
            self.map_view.refresh()

    def _descend(self) -> None:
        sx, sy = self.dungeon.stair_down_pos
        self._floor_stack.append((self.dungeon, sx, sy))
        next_floor = self.dungeon.floor + 1
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
        self.map_view.dungeon = self.dungeon
        self.map_view.refresh()
        self._update_title()
        self.stats_panel.floor_num = self.dungeon.floor
        self.stats_panel.refresh()
        if self.player:
            self.message_log.add(
                f"Ascended to floor {self.dungeon.floor}."
            )
