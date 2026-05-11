from textual.app import App, ComposeResult
from textual.widgets import Static

from .dungeon import generate_dungeon
from .map_view import MapView


class GlyphboundApp(App):
    CSS = """
    Screen {
        background: black;
        layers: base;
    }

    #title-bar {
        width: 100%;
        height: 1;
        background: black;
        content-align: center middle;
        color: ansi_bright_yellow;
        text-style: bold;
    }

    MapView {
        width: 100%;
        height: 1fr;
        background: black;
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
        self.dungeon = generate_dungeon()
        self.map_view = MapView(self.dungeon)
        yield Static("Glyphbound", id="title-bar")
        yield self.map_view

    # --- movement actions ---

    def action_move_up(self)    -> None: self._move(0, -1)
    def action_move_down(self)  -> None: self._move(0,  1)
    def action_move_left(self)  -> None: self._move(-1, 0)
    def action_move_right(self) -> None: self._move(1,  0)

    def _move(self, dx: int, dy: int) -> None:
        self.dungeon.move_party(dx, dy)
        self.map_view.refresh()
