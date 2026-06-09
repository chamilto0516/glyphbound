from textual.app import App, ComposeResult
from textual.widgets import Static

from .dungeon import STAIR_DOWN, STAIR_UP, generate_dungeon
from .map_view import MapView


class GlyphboundApp(App):
    CSS = """
    Screen {
        background: black;
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
        self._floor_stack: list = []  # each entry: (dungeon, stair_down_x, stair_down_y)
        self.map_view = MapView(self.dungeon)
        yield Static("Glyphbound", id="title-bar")
        yield self.map_view

    def on_mount(self) -> None:
        self._update_title()

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

    def _ascend(self) -> None:
        if not self._floor_stack:
            return
        prev_dungeon, stair_x, stair_y = self._floor_stack.pop()
        prev_dungeon.party_x, prev_dungeon.party_y = stair_x, stair_y
        self.dungeon = prev_dungeon
        self.map_view.dungeon = self.dungeon
        self.map_view.refresh()
        self._update_title()
