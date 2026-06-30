# Glyphbound — Complete Game Design Reference

> A terminal-based roguelike written in Python. Use this document to ask creative design and balancing questions, particularly around the upcoming **Glyph system**.

---

## Overview

Glyphbound is a turn-based roguelike played in a terminal (TUI). The player descends through procedurally generated dungeon floors, fighting monsters, collecting items, and spending gold at merchant shops. There is **no going back** — every staircase crumbles the moment you step down it. Each floor is a fresh, one-way trip deeper into the dungeon.

The working title's theme is **runes and magical language** — the dungeon has an ancient, inscribed quality. The planned apex system is the **Glyph system**: collectible magical symbols the player discovers, learns, and casts, with deeper power than standard spells.

---

## Core Mechanics

### Turn Structure
Every player action (move, attack, use item, cast spell, flee) consumes one turn. After the player acts, **every monster on the floor takes a turn**. Combat is not a separate screen — it happens on the map.

- **Bump attack**: walk into a monster to strike it.
- **Map-level ability keys**: `R` Rage, `Z` Spell, `P` Potion, `C` Scroll, `F` Flee — each costs a turn and triggers monster responses.

### One-Way Descent
- Stairs only go **down**. The moment you descend, the stairs crumble behind you — the message reads *"The stairs crumble to dust behind you."*
- Each floor is a **completely new dungeon** — new layout, new monsters, new loot.
- There is no returning to a previous floor. **Death is permanent** (permadeath).

### Field of View (Darkness)
The dungeon is dark. You only see tiles within your **light radius**.

| State | Rendering |
|---|---|
| **Lit** (in current radius) | Full color — monsters, items, traps all visible |
| **Explored** (seen earlier) | Dimmed terrain only — no monsters or items shown |
| **Unseen** (never seen) | Dark grey void |

**Light is blocked by walls and closed doors.** VOID space between corridors also blocks sight — you cannot peek around corners.

---

## Dungeon Generation

Floors are procedurally generated using rooms connected by corridors (minimum spanning tree), with dead-end branch rooms added for variety.

- **Map size**: 100 × 60 tiles
- **Rooms per floor**: 8–14 (varies by theme)
- **Player starts** in the first room; **stairs down** are in the room farthest from the start
- **Shop** appears in the largest eligible room (not start, not stair room), if one is large enough
- **Monster count**: 6 on floor 1, +2 per floor, capped at 24
- **Monsters spawn weighted** toward stronger types on deeper floors
- **Items never overlap stairs** — guaranteed by a ring-search placement algorithm
- **Traps**: 2–5 per floor, scattered in non-start rooms

### Dungeon Themes (6 total)
Each theme changes tile glyphs, colors, room sizes, and corridor lengths. The theme is chosen randomly per floor.

| Theme | Floor glyph | Wall glyph | Door glyph | Palette |
|---|---|---|---|---|
| **Library** | `.` | `#` | `+` | Wheat/navajo — warm yellows |
| **Living Dungeon** | `,` | `O` | `V` | Sea greens |
| **Prison** | `.` | `\|` | `=` | Grey/cyan |
| **Catacombs** | `.` | `*` | `+` | Reds and rose |
| **Ritual Sanctum** | `*` | `#` | `X` | Purples/magenta |
| **Natural Caverns** | `.` | `%` | `+` | Grey/blue-white |

Closed doors are rendered in each theme's **bright accent color** so they stand out clearly.

---

## Character Classes

All classes start with a **Club** (weapon) and **Leather Cap** (helmet) equipped.

### Base Stats by Class

| Class | HP | Attack | Defense | MP | Role |
|---|---|---|---|---|---|
| **Warrior** | 20 | 6 | 4 | 0 | Melee bruiser |
| **Wizard** | 10 | 2 | 1 | 20 | Spellcaster |
| **Thief** | 14 | 4 | 2 | 0 | Skirmisher |
| **Cleric** | 16 | 3 | 3 | 15 | Support/undead hunter |

### Level-Up Gains (per level)

| Class | +HP | +ATK | +DEF | +MP |
|---|---|---|---|---|
| Warrior | 5 | 1 | 1 | — |
| Wizard | 3 | — | — | 5 |
| Thief | 4 | 1 | 1 | — |
| Cleric | 4 | — | 1 | 3 |

MP regenerates 1 per step (movement tile).

### XP Curve

| Level | Cumulative XP needed |
|---|---|
| 2 | 10 |
| 3 | 25 |
| 4 | 75 |
| 5 | 175 |
| 6 | 375 |
| 7 | 775 |

---

## Class Abilities

### Warrior
- **Rage** (once per floor): Double damage for 3 turns. Activates with `R`. Rage carries through dual-wield strikes.
- **Toughness** (passive): 50% chance to absorb 1 point of damage per hit.
- **Dual Wield**: A Warrior with a weapon in the main hand can equip a second weapon in the off-hand (shield slot). This gives **two attacks per turn** — one with each weapon.
- **Heavy gear access**: Only Warriors can equip Warrior-only weapons (Great Sword, War Hammer, Halberd, Maul, Gorecleaver) and armor (Plate Mail, Great Helm, Kite Shield, Gauntlets).

### Wizard
- **Spellcasting** (`Z`): Selects and casts a spell. In bump combat, automatically casts the best affordable damage spell each round instead of using a weapon.
- Spells learned automatically at level thresholds (see Spells section).

### Thief
- **Backstab** (passive): Each level adds 10% chance to deal double damage on a hit (max 100% at level 10).
- **Flee** advantage: 50% base flee chance + 5% per level (cap 100%) vs 25% for other classes.
- **Trap detection** (passive): 10% per level chance to detect traps within 20 tiles when opening a door.
- **Trap disarm**: `X` key. 10% per level success chance on a detected trap.

### Cleric
- **Spellcasting** (`Z`): Healing, buffing, Turn Undead, and damage spells.
- **Turn Undead**: Destroys undead with max HP ≤ 10 outright; deals 50–99% HP damage to stronger undead.

---

## Equipment Slots

Every character has the following equip slots:

| Slot | Key | Notes |
|---|---|---|
| Weapon (main hand) | W | All classes |
| Off-hand / Shield | S | Shield for most; Warriors can dual-wield a second weapon here; anyone can hold a Torch here |
| Body armor | A | |
| Helmet | H | |
| Left ring | RL | Auto-fills left first, then right |
| Right ring | RR | |
| Amulet | N | |
| Boots | B | |
| Gloves | G | |

Equipping an item displaces whatever was in that slot back to inventory. Rings auto-fill: left first, then right; equipping a third ring displaces the left.

---

## Combat

### Attack Resolution
```
Roll 1d6 + attacker ATK  vs  defender DEF
Hit if roll > DEF
Damage = weapon dice roll
```

- Warrior Rage: damage × 2 for up to 3 turns
- Thief Backstab: damage × 2 on a successful proc
- Dual-wield Warrior: two separate attack rolls and damage rolls per turn

### Flee (`F`)
- **Thief**: 50% + 5%/level (cap 100%)
- **Others**: 25% flat
- On success: engaged monsters are **frozen for 3 turns** (skip their AI) so you can run
- On failure: the monster gets a free attack

### Invulnerability
Scroll of Invulnerability makes the player immune to all monster damage for 3 rounds, decrementing each monster attack.

---

## Light & Field of View

### Light Radii

| Source | Radius | Type | Duration | Notes |
|---|---|---|---|---|
| Base vision | 3 | Passive | Always | Every character |
| Torch (lit) | 12 | Equipped (off-hand) | Whole floor | Burns out: 50% chance after >30 damage in one fight; consumed on unequip |
| Sunblade | 8 | Equipped (weapon) | While equipped | Unique item; light + combat stats |
| Aegis of Dawn | 8 | Equipped (off-hand/shield) | While equipped | Unique; light + defense |
| Starlit Helm | 10 | Equipped (helmet) | While equipped | Unique; best passive light |
| Scroll of Illumination | 18 | Read | Whole floor | Floor-wide ambient light; no hand needed |
| Illumination spell | 15 | Cast | Whole floor | Wizard level 2+; costs 4 MP |

**Radii do not stack.** The effective radius is `max(player's equipped light, floor ambient light)`.

**`--light` flag**: launch the game with `python main.py --light` to reveal the entire map (debug mode).

---

## Weapons

### Standard Weapons (all classes)

| Weapon | ATK bonus | Damage | Value |
|---|---|---|---|
| Club | +1 | 1 (static) | 2 gp |
| Dagger | +2 | 1d4 | 5 gp |
| Staff | +2 | 1d4 | 8 gp |
| Mace | +2 | 1d6 | 12 gp |
| Short Sword | +3 | 1d6 | 15 gp |
| Broad Sword | +4 | 1d8 | 30 gp |
| Long Sword | +4 | 1d10 | 40 gp |
| Battle Axe | +5 | 2d6 | 60 gp |

### Warrior-Only Heavy Weapons

| Weapon | ATK bonus | Damage | Value |
|---|---|---|---|
| Maul | +4 | 3d6 | 60 gp |
| War Hammer | +5 | 2d8 | 70 gp |
| Great Sword | +6 | 1d12 | 80 gp |
| Halberd | +7 | 2d10 | 100 gp |

### Unique Weapons

| Weapon | ATK bonus | Damage | Value | Notes |
|---|---|---|---|---|
| Fang | +3 | 1d6 | 80 gp | Unique |
| Flamebrand | +5 | 1d10 | 150 gp | Unique |
| Gorecleaver | +8 | 2d12 | 250 gp | Unique, Warrior-only |
| Sunblade | +4 | 1d8 | 180 gp | Unique; light radius 8 |

### Torch (Light Weapon)
Held in the off-hand (shield slot). Light radius 12. Deals 1 damage if used to attack. Consumed when unequipped. Can burn out (50% chance) if the player takes more than 30 cumulative damage in a single combat engagement.

---

## Armor

### Standard Armor (all classes)

| Item | Slot | DEF bonus | Value |
|---|---|---|---|
| Leather Cap | Helmet | +1 | 4 gp |
| Iron Helm | Helmet | +2 | 15 gp |
| Leather Armor | Body | +2 | 10 gp |
| Chain Mail | Body | +3 | 30 gp |
| Small Shield | Off-hand | +1 | 8 gp |
| Tower Shield | Off-hand | +2 | 25 gp |
| Leather Boots | Boots | +1 | 20 gp |
| Iron Boots | Boots | +2 | 40 gp |
| Leather Gloves | Gloves | +1 ATK | 18 gp |
| Thief's Gloves | Gloves | +2 ATK | 60 gp |

### Warrior-Only Armor

| Item | Slot | DEF bonus | Value |
|---|---|---|---|
| Great Helm | Helmet | +4 | 70 gp |
| Plate Mail | Body | +6 | 120 gp |
| Kite Shield | Off-hand | +4 | 80 gp |
| Gauntlets | Gloves | +1 DEF, +1 ATK | 50 gp |

### Accessories (rings, amulet)

| Item | Slot | Effect | Value |
|---|---|---|---|
| Ring of Protection | Ring | +1 DEF | 50 gp |
| Ring of Clarity | Ring | +5 max MP | 60 gp |
| Amulet of Vitality | Amulet | +5 max HP | 60 gp |
| Boots of Speed | Boots | — (flavor) | 45 gp |

### Unique Armor / Magic Light Items

| Item | Slot | Effect | Value |
|---|---|---|---|
| Starlit Helm | Helmet | +2 DEF, light radius 10 | 150 gp |
| Aegis of Dawn | Off-hand/Shield | +3 DEF, light radius 8 | 160 gp |

---

## Potions

Potions sit in inventory and are consumed with `P`. Level-up is checked after drinking.

| Potion | Effect | Value |
|---|---|---|
| Health Potion | +10 HP | 20 gp |
| Mana Potion | +10 MP | 20 gp |
| Potion of Knowledge | +10 XP (can trigger level-up) | 35 gp |
| Elixir of Vitality | Full HP restore | 80 gp |
| Elixir of Clarity | Full MP restore | 80 gp |

---

## Scrolls

Scrolls are read with `C`. Consumed on use.

| Scroll | Effect | Value |
|---|---|---|
| Scroll of Fireball | 3d6 fire damage to nearest monster | 40 gp |
| Scroll of Heal | +20 HP | 30 gp |
| Scroll of Invulnerability | Immune to damage for 3 turns | 60 gp |
| Scroll of Illumination | Lights the whole floor (radius 18, blocked by walls/doors) for the rest of the floor | 45 gp |

---

## Spells

Spells are cast with `Z` (opens a selection screen). Wizards auto-cast the best available damage spell when bump-attacking in combat.

### Wizard Spells

| Spell | Level | MP | Effect |
|---|---|---|---|
| Magic Bolt | 1 | 2 | 1d6 damage |
| Magic Armor | 1 | 3 | +1d10 DEF for next combat |
| Detect Magic | 1 | 2 | Reveals all magical traps on the floor |
| Blink | 1 | 4 | Short-range teleport (escape combat) — not yet fully implemented |
| Fireball | 2 | 5 | 1d10 damage |
| **Illumination** | **2** | **4** | **Lights the floor (radius 15) for the rest of the floor** |
| Lightning Bolt | 3 | 6 | 2d6 damage |
| Shield | 4 | 5 | +2d10 DEF for next combat |
| Meteor Swarm | 5 | 8 | 3d8 damage |
| Arcane Blast | 6 | 10 | 3d10 damage |
| Time Stop | 7 | 12 | +2d20 DEF for next combat |

### Cleric Spells

| Spell | Level | MP | Effect |
|---|---|---|---|
| Heal | 1 | 4 | 2d6 HP restored |
| Smite | 1 | 3 | 1d8 holy damage |
| Bless | 1 | 3 | +1d6 ATK for next combat |
| Sanctuary | 1 | 4 | +1d8 DEF for next combat |
| Turn Undead | 2 | 5 | Destroys weak undead (≤10 HP); 50–99% damage to stronger undead |
| Light from Heaven | 3 | 6 | 2d8 holy damage |
| Greater Heal | 4 | 7 | 4d6 HP restored |
| Divine Shield | 5 | 6 | +2d10 DEF for next combat |
| Holy Fire | 6 | 9 | 3d10 holy damage |
| Wrath of Heaven | 7 | 10 | 4d8 holy damage |

---

## Treasure (auto-converted on pickup)

All treasure items are consumed immediately when stepped on — they never sit in inventory.

| Item | Gold | Other effect |
|---|---|---|
| Gold Coins | 5 gp | — |
| Gold Pile | 15 gp | — |
| Large Gold Pile | 30 gp | — |
| Gem | 50 gp | — |
| Ornate Rug | 15 gp | — |
| Silver Candlestick | 20 gp | — |
| Ink Vial | 35 gp | — |
| Ancient Tome | 40 gp | — |
| Idol | 60 gp | — |
| Cracked Rune Fragment | 0 gp | +5 XP — thematic: lore fragments that teach you something |
| Blessed Chalice | 15 gp | +5 HP on pickup |

---

## Shop

A merchant's stall appears on most floors (in the largest room, if large enough). Stock scales with floor depth. Players buy items for their gold value.

| Floor | Items available |
|---|---|
| 1+ | Health Potion, Mana Potion, Torch, Scroll of Illumination |
| 2+ | + Elixir of Vitality, Elixir of Clarity |
| 3+ | + Dagger, Short Sword, Mace |
| 4+ | + Leather Armor, Small Shield, Iron Helm, Leather Boots, Leather Gloves |
| 5+ | + Broad Sword, Long Sword, Ring of Protection |
| 6+ | + Chain Mail, Scroll of Heal, Scroll of Invulnerability, Iron Boots, Gauntlets |
| 7+ | + Battle Axe, Scroll of Fireball, Boots of Speed, Thief's Gloves |

---

## Traps

Traps are hidden until detected. They trigger when stepped on.

- **Types**: Spike, Dart, Teleport, Alarm, Summoning, Silence, Confusion (exact damage varies by type)
- **Detection**: Thieves detect traps within 20 tiles when opening doors (10% per level chance)
- **Disarming**: Thieves only (`X` key), 10% per level success chance on a detected trap
- **Trigger**: Deals damage, removes the trap. Damage goes to the death-screen last-messages log.

---

## Monsters

Spawn counts: floor 1 = 6 monsters; each additional floor adds 2; capped at 24. Monster strength is weighted toward stronger types on deeper floors.

### All Monsters

| Monster | Glyph | Floor | HP | ATK | DEF | XP | Undead | Weapon | AI |
|---|---|---|---|---|---|---|---|---|---|
| Goblin | `g` | 1+ | 5 | 1 | 1 | 1 | — | Club | Wander |
| Skeleton | `s` | 1+ | 8 | 2 | 1 | 2 | ☠ | Short Sword | Wander |
| Orc | `o` | 2+ | 12 | 3 | 2 | 3 | — | Short Sword | Wander |
| Zombie | `z` | 2+ | 15 | 4 | 2 | 4 | ☠ | Club | Wander |
| Bugbear | `b` | 2+ | 18 | 4 | 2 | 5 | — | Mace | Wander |
| Troll | `T` | 3+ | 25 | 5 | 3 | 7 | — | Broad Sword | Guard |
| Mummy | `M` | 3+ | 20 | 5 | 4 | 8 | ☠ | claws | Wander |
| Wight | `W` | 3+ | 18 | 6 | 3 | 9 | ☠ | Long Sword | Wander |
| Owlbear | `O` | 4+ | 30 | 7 | 4 | 12 | — | claws/beak | Guard |
| Wraith | `"` | 4+ | 22 | 7 | 5 | 14 | ☠ | claws | Wander |
| Umber Hulk | `U` | 5+ | 40 | 8 | 5 | 18 | — | claws | Guard |
| Vampire | `V` | 5+ | 35 | 9 | 6 | 22 | ☠ | claws | Wander |
| Dragon | `D` | 7+ | 60 | 12 | 8 | 50 | — | claws/fire | Guard |

**Undead (☠)**: Vulnerable to Cleric's Turn Undead. Skeleton, Zombie, Mummy, Wight, Wraith, Vampire.

### Monster AI States
- **Wander**: Random movement; switches to Chase when player is within `chase_range` tiles
- **Guard**: Returns to spawn point if too far; switches to Chase when player is within `chase_range`
- **Chase**: Moves directly toward player; attacks when adjacent
- **Frozen**: After a successful player Flee, monsters freeze for 3 turns (skip AI turn)

### Monster Loot (samples)
- Goblin: small gold, 10% common weapon
- Skeleton: small gold, 15% weapon/armor
- Troll: large gold, 30% weapon, 20% armor
- Wraith: Gem, 25% accessory
- Vampire: Gem + large gold, 40% accessory, 25% rare weapon
- Dragon: 2× large gold, Gem, guaranteed rare item + 50% accessory + 30% elixir

**Guaranteed drop**: The first monster spawned on **floor 1 only** always carries a Torch — ensuring a new player always has access to light.

---

## Death Screen

When the player dies, a death screen shows:
- Name, class, floor of death
- Final stats: level, XP, gold, floors descended, squares traveled, monsters killed, damage taken, items found, MP spent
- **Last 5 message log entries** (in red) — so the player can see the trap or monster hit that killed them

Press `Q` to quit or `R` to restart a new run.

---

## What Does Not Yet Exist (planned)

The following are designed but not yet implemented. This is context for what the **Glyph system** needs to integrate with:

- **Glyph system** — the game's signature mechanic. Collectible magical runes the player discovers, learns, and casts. Planned glyph types: Reveal, Bind, Break, Move, Light, Name, Rewrite, Seal. Glyph-themed enemies (Ink Wraith, Syntax Serpent, Living Rune, Null Beast) will tie into this.
- **Ranged combat / spellcaster enemies**
- **Status effects** (poison, frozen, burning, bound, confused)
- **Boss encounters** at floor milestones
- **Save / load** (permadeath is the default; no save currently)
- **FOV fog of war persistence between floors** (each floor starts fresh)
- **Blink spell** (coded, not fully wired)
- **Secret rooms and hidden passages**
- **Item identification system** (unidentified potions/scrolls)
- **True-name mechanics** for weakening special enemies

---

## Key Design Constraints to Keep in Mind

1. **One-way dungeon** — no coming back up. Every decision is permanent for that floor.
2. **Darkness is the default** — base vision is only 3 tiles. Light sources are a meaningful resource.
3. **Combat is on the map** — no separate combat screen. Every action has an opportunity cost because monsters are acting too.
4. **Four very different classes** — Warrior (physical tank), Wizard (fragile caster), Thief (glass cannon + utility), Cleric (sustain + undead specialty). The Glyph system should feel useful to all four, but differently.
5. **Gold has a use** — the shop is the gold sink. Glyphs could potentially be bought, sold, or upgraded there.
6. **Equipment slots are limited** — the off-hand choice (shield vs. torch vs. second weapon for Warriors) is already a real tradeoff. Glyphs should not trivially override this.
