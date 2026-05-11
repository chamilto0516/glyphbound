from rich.segment import Segment
from rich.style import Style
from textual.strip import Strip
from textual.widget import Widget

from .dungeon import (
    Dungeon, VOID, FLOOR, WALL, DOOR_CLOSED, DOOR_OPEN,
    TILE_GLYPHS, PARTY_GLYPH,
)

_BG = "black"

TILE_STYLES = {
    VOID:        Style(color="black",       bgcolor=_BG),
    FLOOR:       Style(color="yellow4",     bgcolor=_BG),
    WALL:        Style(color="yellow",      bgcolor=_BG, bold=True),
    DOOR_CLOSED: Style(color="orange3",     bgcolor=_BG, bold=True),
    DOOR_OPEN:   Style(color="dark_orange", bgcolor=_BG),
}
PARTY_STYLE = Style(color="bright_yellow", bgcolor=_BG, bold=True)


class MapView(Widget):

    def __init__(self, dungeon: Dungeon) -> None:
        super().__init__()
        self.dungeon = dungeon

    def render_line(self, y: int) -> Strip:
        width  = self.size.width
        height = self.size.height
        if not width or not height:
            return Strip([])

        dungeon = self.dungeon
        # Viewport top-left, clamped to map bounds
        vx = max(0, min(dungeon.party_x - width  // 2, dungeon.width  - width))
        vy = max(0, min(dungeon.party_y - height // 2, dungeon.height - height))

        my = vy + y
        segments = []
        for col in range(width):
            mx = vx + col
            if mx == dungeon.party_x and my == dungeon.party_y:
                segments.append(Segment(PARTY_GLYPH, PARTY_STYLE))
            else:
                tile  = dungeon.tile_at(mx, my)
                segments.append(Segment(TILE_GLYPHS[tile], TILE_STYLES[tile]))

        return Strip(segments, width)
