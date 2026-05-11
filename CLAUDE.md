# Glyphbound — Claude Code Project Guide

## What We Are Building

Glyphbound is a terminal-based roguelike adventure game written in Python using the Textual TUI framework. The player explores procedurally generated dungeons, fights monsters, collects items, and progresses through increasingly difficult floors. The "glyph" theme ties into runic/magical symbols that power abilities and lore.

## Tech Stack

| Tool / Library | Purpose |
|---|---|
| Python 3.9+ | Primary language |
| [Textual](https://github.com/Textualize/textual) | TUI framework — widgets, layout, input, rendering |
| [Rich](https://github.com/Textualize/rich) | Terminal styling (pulled in by Textual) |
| `venv` | Dependency isolation (`.venv/` at project root) |
| `git` + GitHub | Version control (`chamilto0516/glyphbound`) |

## Project Structure

```
glyphbound/
├── main.py               # Entry point — run this to start the game
├── requirements.txt      # Pip dependencies
├── CLAUDE.md             # This file
├── README.md             # Project overview
├── .venv/                # Virtual environment (not committed)
└── glyphbound/           # Game package
    ├── __init__.py
    └── app.py            # GlyphboundApp (Textual App subclass)
```

As the project grows, new modules go inside `glyphbound/`:
- `map.py` — dungeon/map generation
- `entities.py` — player, monsters, NPCs
- `combat.py` — combat resolution
- `items.py` — inventory and items
- `ui/` — reusable Textual widgets and screens

## How to Run

```bash
# First time only — activate the virtual environment
source .venv/bin/activate

# Run the game
python main.py
```

The venv must be active for `python` to resolve correctly. Your prompt will show `(.venv)` when it is active. To exit the venv, run `deactivate`.

You can also run without activating:
```bash
.venv/bin/python main.py
```

## How to Add Dependencies

```bash
source .venv/bin/activate
pip install <package>
pip freeze > requirements.txt   # keep this in sync
```

## Future Feature Ideas

- [ ] Procedurally generated dungeon floors (rooms + corridors)
- [ ] Field-of-view / fog of war
- [ ] Player character with stats (HP, attack, defense, level)
- [ ] XP and leveling system
- [ ] Multiple monster types with simple AI
- [ ] Melee and ranged combat
- [ ] Inventory system and item pickup
- [ ] Glyph-based ability system (runes that grant powers)
- [ ] Scrolls, potions, and equipment
- [ ] Traps and environmental hazards
- [ ] Persistent high score / death log
- [ ] Multiple dungeon themes / tilesets (in ASCII)
- [ ] Boss encounters at floor milestones
- [ ] Save and load game state
- [ ] Sound effects (via system bell or external library)
- [ ] Config file for keybindings and display options
