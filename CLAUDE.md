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

# Glyphbound Future Feature Ideas

## Dungeon Generation
- [ ] Procedurally generated dungeon floors with rooms and corridors
- [ ] Multiple dungeon themes: library, catacombs, ritual halls, corrupted syntax, deep archive
- [ ] Room types: combat, treasure, Glyph, trap, lore, rest, boss
- [ ] Floor progression with stairs, milestones, and escalating danger
- [ ] Seeded dungeon generation for replay/debugging
- [ ] Secret rooms and hidden passages
- [ ] Dungeon “grammar” rules where rooms, corridors, and Glyphs interact thematically

## Field of View and Map Knowledge
- [ ] Field-of-view / line-of-sight system
- [ ] Fog of war with explored vs visible tiles
- [ ] Light radius and darkness effects
- [ ] Map-revealing Glyphs and scrolls
- [ ] Hidden traps, doors, enemies, and inscriptions
- [ ] Debug reveal-map mode

## Player Character
- [ ] Player stats: HP, attack, defense, level, XP, focus, Glyph power
- [ ] Character archetypes such as Reader, Scribe, Warden, and Seeker
- [ ] Level-up choices and stat upgrades
- [ ] Passive traits or talents
- [ ] Run summary stats: kills, floor reached, Glyphs learned, cause of death

## Monsters and AI
- [ ] Multiple monster types with different stats and symbols
- [ ] Simple AI: wander, chase, flee, guard, patrol
- [ ] Ranged enemies and spellcasters
- [ ] Glyph-themed enemies: Ink Wraith, Syntax Serpent, Living Rune, Null Beast
- [ ] Monster status effects
- [ ] Spawn tables by floor and dungeon theme
- [ ] Named elite monsters

## Combat
- [ ] Melee bump combat
- [ ] Ranged combat and targeting
- [ ] Damage types and armor/defense calculations
- [ ] Critical hits, misses, knockback, and evasion
- [ ] Status effects: burning, frozen, poisoned, bound, silenced, confused, vulnerable
- [ ] Area-of-effect attacks
- [ ] Combat log messages

## Glyph System
- [ ] Glyph collection and discovery
- [ ] Glyph screen showing known Glyphs
- [ ] Castable Glyph abilities
- [ ] Focus or cooldown cost for Glyph use
- [ ] Targeting rules for each Glyph
- [ ] Glyph types: Reveal, Bind, Break, Move, Light, Name, Rewrite, Seal
- [ ] Glyph combinations
- [ ] Glyph upgrades
- [ ] Glyph interactions with traps, walls, doors, monsters, and items
- [ ] True-name mechanics for weakening special enemies

## Inventory and Items
- [ ] Inventory system
- [ ] Item pickup, drop, use, inspect
- [ ] Stackable consumables
- [ ] Equipment slots for weapon, armor, ring, amulet, cloak, tome
- [ ] Potions, scrolls, weapons, armor, charms, tomes, and Glyph stones
- [ ] Item identification system
- [ ] Random item generation and rarity tables
- [ ] Unique artifacts

## Traps and Hazards
- [ ] Hidden and visible traps
- [ ] Spike, dart, teleport, alarm, summoning, silence, and confusion traps
- [ ] Environmental hazards: chasms, cursed ink, darkness, poison gas, unstable glyph fields
- [ ] Trap detection and disarming
- [ ] Glyph-based trap manipulation

## Bosses
- [ ] Boss encounters at floor milestones
- [ ] Boss arenas
- [ ] Multi-phase boss fights
- [ ] Bosses with Glyph-specific mechanics
- [ ] Unique boss rewards
- [ ] Final boss: the dungeon as a living sentence or language
- [ ] Multiple endings based on Glyph knowledge

## Save, Load, and Persistence
- [ ] Save and load current game state
- [ ] Autosave on floor transition
- [ ] Permadeath mode
- [ ] Optional adventure mode with reloads
- [ ] Persistent high score table
- [ ] Death log / graveyard
- [ ] Persistent codex for discovered Glyphs, monsters, and lore

## UI and Screens
- [ ] Main menu
- [ ] Help/controls screen
- [ ] Inventory screen
- [ ] Equipment screen
- [ ] Glyph screen
- [ ] Level-up screen
- [ ] Look/examine mode
- [ ] Targeting cursor
- [ ] Death screen
- [ ] Run summary screen
- [ ] Message log improvements

## Controls and Config
- [ ] Config file for keybindings
- [ ] Config file for display options
- [ ] Toggle color mode
- [ ] Toggle sound
- [ ] Support arrow keys, numpad, and vi keys
- [ ] Debug/developer commands

## Sound and Feedback
- [ ] System bell sound effects
- [ ] Optional external sound library support
- [ ] Hit, death, pickup, trap, level-up, and Glyph-cast feedback
- [ ] Screen flash or visual emphasis for major events
- [ ] Configurable mute option

## Lore and Language
- [ ] Procedural inscriptions
- [ ] Glyph dictionary
- [ ] Lore fragments
- [ ] Monster true names
- [ ] Room names and floor titles
- [ ] Boss dialogue
- [ ] Death epitaphs
- [ ] Codex entries unlocked across runs

## Architecture and Programmatic Systems
- [ ] Game state manager
- [ ] Turn manager
- [ ] Entity system for player, monsters, items, traps, stairs, and effects
- [ ] Event queue
- [ ] Message log system
- [ ] Input command abstraction
- [ ] Rendering abstraction
- [ ] Save/load serialization layer
- [ ] Data-driven definitions for monsters, items, Glyphs, bosses, and themes
- [ ] Random number generator wrapper for seeded runs
- [ ] Error logging

## Testing and Debugging
- [ ] Unit tests for movement, combat, items, Glyphs, and map generation
- [ ] Map connectivity validator
- [ ] Save/load roundtrip tests
- [ ] Debug reveal-map command
- [ ] Debug spawn monster/item/Glyph commands
- [ ] God mode
- [ ] Jump-to-floor debug command
- [ ] Combat simulator for balancing
- [ ] Print current map seed

## Balance and Difficulty
- [ ] Floor-based difficulty scaling
- [ ] Monster spawn budgets
- [ ] Item rarity and loot tables
- [ ] XP curve
- [ ] Healing availability tuning
- [ ] Trap density tuning
- [ ] Boss difficulty scaling
- [ ] Optional corruption/pressure clock