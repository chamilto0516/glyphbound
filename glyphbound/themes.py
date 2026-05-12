from dataclasses import dataclass
from typing import Dict

from rich.style import Style

from .dungeon import VOID, FLOOR, WALL, DOOR_CLOSED, DOOR_OPEN

PARTY_GLYPH = "@"

_BG = "black"


@dataclass(frozen=True)
class Theme:
    name: str
    glyphs: Dict[int, str]
    tile_styles: Dict[int, Style]
    party_style: Style
    title_color: str
    min_rooms: int
    max_rooms: int
    min_room_w: int
    max_room_w: int
    min_room_h: int
    max_room_h: int
    max_corridor: int = 150


THEME_LIBRARY = Theme(
    name="Library",
    glyphs={VOID: " ", FLOOR: ".", WALL: "#", DOOR_CLOSED: "+", DOOR_OPEN: "/"},
    tile_styles={
        VOID:        Style(color="black",        bgcolor=_BG),
        FLOOR:       Style(color="wheat4",        bgcolor=_BG),
        WALL:        Style(color="navajo_white1", bgcolor=_BG, bold=True),
        DOOR_CLOSED: Style(color="sandy_brown",   bgcolor=_BG, bold=True),
        DOOR_OPEN:   Style(color="tan",           bgcolor=_BG),
    },
    party_style=Style(color="bright_yellow", bgcolor=_BG, bold=True),
    title_color="ansi_bright_yellow",
    min_rooms=12, max_rooms=18,
    min_room_w=8, max_room_w=18,
    min_room_h=5, max_room_h=12,
    max_corridor=160,
)

THEME_LIVING = Theme(
    name="Living Dungeon",
    glyphs={VOID: " ", FLOOR: ",", WALL: "O", DOOR_CLOSED: "V", DOOR_OPEN: "v"},
    tile_styles={
        VOID:        Style(color="black",          bgcolor=_BG),
        FLOOR:       Style(color="dark_sea_green4", bgcolor=_BG),
        WALL:        Style(color="pale_green3",     bgcolor=_BG, bold=True),
        DOOR_CLOSED: Style(color="sea_green3",      bgcolor=_BG, bold=True),
        DOOR_OPEN:   Style(color="chartreuse4",     bgcolor=_BG),
    },
    party_style=Style(color="bright_green", bgcolor=_BG, bold=True),
    title_color="ansi_bright_green",
    min_rooms=10, max_rooms=16,
    min_room_w=6, max_room_w=20,
    min_room_h=4, max_room_h=14,
    max_corridor=170,
)

THEME_JAIL = Theme(
    name="Prison",
    glyphs={VOID: " ", FLOOR: ".", WALL: "|", DOOR_CLOSED: "=", DOOR_OPEN: "-"},
    tile_styles={
        VOID:        Style(color="black",   bgcolor=_BG),
        FLOOR:       Style(color="grey46",  bgcolor=_BG),
        WALL:        Style(color="grey66",  bgcolor=_BG, bold=True),
        DOOR_CLOSED: Style(color="grey70",  bgcolor=_BG, bold=True),
        DOOR_OPEN:   Style(color="grey37",  bgcolor=_BG),
    },
    party_style=Style(color="bright_white", bgcolor=_BG, bold=True),
    title_color="ansi_bright_white",
    min_rooms=14, max_rooms=22,
    min_room_w=4, max_room_w=8,
    min_room_h=3, max_room_h=6,
    max_corridor=140,
)

THEME_CATACOMBS = Theme(
    name="Catacombs",
    glyphs={VOID: " ", FLOOR: ".", WALL: "*", DOOR_CLOSED: "+", DOOR_OPEN: "/"},
    tile_styles={
        VOID:        Style(color="black",       bgcolor=_BG),
        FLOOR:       Style(color="rosy_brown",  bgcolor=_BG),
        WALL:        Style(color="indian_red1", bgcolor=_BG, bold=True),
        DOOR_CLOSED: Style(color="dark_red",    bgcolor=_BG, bold=True),
        DOOR_OPEN:   Style(color="rosy_brown",  bgcolor=_BG),
    },
    party_style=Style(color="bright_red", bgcolor=_BG, bold=True),
    title_color="ansi_bright_red",
    min_rooms=12, max_rooms=18,
    min_room_w=5, max_room_w=12,
    min_room_h=4, max_room_h=9,
    max_corridor=160,
)

THEME_RITUAL = Theme(
    name="Ritual Sanctum",
    glyphs={VOID: " ", FLOOR: "*", WALL: "#", DOOR_CLOSED: "X", DOOR_OPEN: "x"},
    tile_styles={
        VOID:        Style(color="black",          bgcolor=_BG),
        FLOOR:       Style(color="medium_purple3", bgcolor=_BG),
        WALL:        Style(color="plum4",          bgcolor=_BG, bold=True),
        DOOR_CLOSED: Style(color="orchid1",        bgcolor=_BG, bold=True),
        DOOR_OPEN:   Style(color="magenta3",       bgcolor=_BG),
    },
    party_style=Style(color="bright_magenta", bgcolor=_BG, bold=True),
    title_color="ansi_bright_magenta",
    min_rooms=10, max_rooms=16,
    min_room_w=7, max_room_w=16,
    min_room_h=5, max_room_h=12,
    max_corridor=170,
)

THEME_CAVERNS = Theme(
    name="Natural Caverns",
    glyphs={VOID: " ", FLOOR: ".", WALL: "%", DOOR_CLOSED: "+", DOOR_OPEN: "/"},
    tile_styles={
        VOID:        Style(color="black",           bgcolor=_BG),
        FLOOR:       Style(color="grey37",          bgcolor=_BG),
        WALL:        Style(color="grey58",          bgcolor=_BG, bold=True),
        DOOR_CLOSED: Style(color="steel_blue",      bgcolor=_BG, bold=True),
        DOOR_OPEN:   Style(color="cornflower_blue", bgcolor=_BG),
    },
    party_style=Style(color="bright_cyan", bgcolor=_BG, bold=True),
    title_color="ansi_cyan",
    min_rooms=11, max_rooms=17,
    min_room_w=8, max_room_w=24,
    min_room_h=6, max_room_h=16,
    max_corridor=160,
)

ALL_THEMES = [
    THEME_LIBRARY,
    THEME_LIVING,
    THEME_JAIL,
    THEME_CATACOMBS,
    THEME_RITUAL,
    THEME_CAVERNS,
]
