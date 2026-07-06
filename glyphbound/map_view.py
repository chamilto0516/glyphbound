from rich.segment import Segment
from rich.style import Style as RichStyle
from textual.strip import Strip
from textual.widget import Widget

from .dungeon import Dungeon
from .themes import PARTY_GLYPH

_BLANK_STYLE = RichStyle(color="grey11", bgcolor="grey11")


class MapView(Widget):

    def __init__(self, dungeon: Dungeon, reveal_all: bool = False) -> None:
        super().__init__()
        self.dungeon = dungeon
        self.reveal_all = reveal_all   # --light debug flag: show the whole map
        self._dim_cache: dict = {}
        self.targeting_cursor: tuple | None = None
        self.targeting_aoe_radius: int = 0
        self.targeting_valid: bool = True

    def _dim(self, style: RichStyle) -> RichStyle:
        """A dimmed variant of a tile style for explored-but-unseen terrain."""
        cached = self._dim_cache.get(style)
        if cached is None:
            cached = style + RichStyle(dim=True, bold=False)
            self._dim_cache[style] = cached
        return cached

    def refresh(self, *args, **kwargs):
        """Recompute the field of view before every repaint.

        Every game-state change already calls map_view.refresh(), so this is
        the single place that keeps the visible/explored sets current.
        """
        dungeon = getattr(self, "dungeon", None)
        if dungeon is not None and dungeon.theme is not None:
            from .player import Player  # local import avoids a cycle
            app = self.app if self.is_mounted else None
            player = getattr(app, "player", None) if app else None
            light = player.light_radius if isinstance(player, Player) else 5
            dungeon.recompute_visibility(light, reveal_all=self.reveal_all)
        return super().refresh(*args, **kwargs)

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
            lit       = (mx, my) in dungeon.visible
            explored  = (mx, my) in dungeon.explored

            if not lit and not explored:
                # Never seen — dark grey void.
                segments.append(Segment(" ", _BLANK_STYLE))
                continue

            if not lit:
                # Explored but dark: terrain memory only, no monsters/items.
                tile = dungeon.tile_at(mx, my)
                segments.append(Segment(theme.glyphs[tile], self._dim(theme.tile_styles[tile])))
                continue

            # Fully lit — full detail.
            if mx == dungeon.party_x and my == dungeon.party_y:
                glyph_char, style = PARTY_GLYPH, theme.party_style
            else:
                monster = dungeon.monster_at(mx, my)
                if monster:
                    glyph_char, style = monster.glyph, RichStyle(color="bright_red", bold=True)
                else:
                    trap = dungeon.trap_at(mx, my)
                    if trap and trap.is_detected:
                        glyph_char, style = "T", RichStyle(color="red", bold=True)
                    else:
                        floor_items = dungeon.items_at(mx, my)
                        if floor_items:
                            glyph_char, style = floor_items[-1].glyph, RichStyle(color="bright_cyan", bold=True)
                        else:
                            tile = dungeon.tile_at(mx, my)
                            glyph_char, style = theme.glyphs[tile], theme.tile_styles[tile]

            cursor = self.targeting_cursor
            if cursor is not None and (mx, my) == cursor:
                style = RichStyle(
                    color="black",
                    bgcolor="bright_green" if self.targeting_valid else "bright_red",
                    bold=True,
                )
            elif (
                cursor is not None
                and self.targeting_aoe_radius > 0
                and max(abs(mx - cursor[0]), abs(my - cursor[1])) <= self.targeting_aoe_radius
            ):
                style = style + RichStyle(bgcolor="rgb(90,20,20)")

            segments.append(Segment(glyph_char, style))

        return Strip(segments, width)
