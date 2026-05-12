from rich.segment import Segment
from textual.strip import Strip
from textual.widget import Widget

from .dungeon import Dungeon
from .themes import PARTY_GLYPH


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
        theme   = dungeon.theme

        vx = max(0, min(dungeon.party_x - width  // 2, dungeon.width  - width))
        vy = max(0, min(dungeon.party_y - height // 2, dungeon.height - height))

        my = vy + y
        segments = []
        for col in range(width):
            mx = vx + col
            if mx == dungeon.party_x and my == dungeon.party_y:
                segments.append(Segment(PARTY_GLYPH, theme.party_style))
            else:
                tile = dungeon.tile_at(mx, my)
                segments.append(Segment(theme.glyphs[tile], theme.tile_styles[tile]))

        return Strip(segments, width)
