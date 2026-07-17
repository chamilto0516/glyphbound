# Glyphbound — Complete Game Design Reference

> A terminal-based roguelike written in Python. This document is the balancing reference — every table below is extracted from the current code (player/spells/items/monsters/combat/bosses/traps/status_effects/dungeon). Use it to review whether each class, spell, item, and monster is fair and fun. The planned apex system is the **Glyph system** (not yet implemented).

> **Refreshed 2026-07-14** to match the code after the ranged-combat, status-effects, monster-scaling, and boss releases. Numbers here reflect the code, not the older design intent — where the code diverged from the previous doc, the code wins.

---

## Overview

Glyphbound is a turn-based roguelike played in a terminal (TUI). The player descends through procedurally generated dungeon floors, fighting monsters, collecting items, and spending gold at merchant shops. There is **no going back** — every staircase crumbles the moment you step down it. Death is permanent.

---

## Core Mechanics

### Turn Structure
Every player action (move, attack, use item, cast spell, throw/shoot, flee) consumes one turn. After the player acts, **every monster on the floor takes a turn**. Combat happens on the map — no separate combat screen.

- **Bump attack**: walk into a monster to strike it.
- **Map-level ability keys**: `R` Rage, `E` Envenom, `Z` Spell, `T` Ranged/Throw, `P` Potion, `C` Scroll, `F` Flee, `X` Disarm trap — each costs a turn and triggers monster responses.
- Status effects tick at the start of an entity's turn (see Status Effects).

### One-Way Descent
- Stairs only go **down**; they crumble behind you. Each floor is a completely new dungeon. Permadeath.

### Field of View (Darkness)
Base vision is only **3 tiles**. Light sources are a real resource.

| State | Rendering |
|---|---|
| **Lit** (in current radius) | Full color — monsters, items, traps visible |
| **Explored** (seen earlier) | Dimmed terrain only |
| **Unseen** | Dark grey void |

Light is blocked by walls and closed doors (recursive shadowcasting). **Radii do not stack** — effective radius is `max(equipped light, floor ambient light)`. `python main.py --light` reveals the whole map (debug).

---

## Dungeon Generation

- **Map size**: 100 × 60 tiles
- **Rooms per floor**: 8–14 (Prison 10–14), MST-connected, plus dead-end branch rooms
- **Player starts** in room 0; **stairs down** are in the farthest room; **shop** in the largest eligible room
- **Monster count**: `min(6 + (floor-1)*2, 24)` → 6 on F1, capped at 24 by floor 10
- **Spawn weighting**: eligible spawners are filtered by `min_floor`; the stronger half of the eligible list gets weight `1 + floor//2`, the weaker half weight `1`. Weaker monsters land nearer the start (rooms sorted near→far).
- **Traps**: `randint(2, 5)` per floor, in non-start rooms
- **Bosses**: floors **3, 5, 10** — one guards the down-stair (see Bosses)

### Dungeon Themes (6 total)
Theme is chosen randomly per floor; changes glyphs, palette, room sizes, corridor length, and which boss pair appears.

| Theme | Floor | Wall | Door | Rooms | Palette |
|---|---|---|---|---|---|
| **Library** | `.` | `#` | `+` | 8–14 | Wheat/navajo warm yellows |
| **Living Dungeon** | `,` | `O` | `V` | 8–14 | Sea greens |
| **Prison** | `.` | `\|` | `=` | 10–14 | Grey/cyan |
| **Catacombs** | `.` | `*` | `+` | 8–14 | Reds and rose |
| **Ritual Sanctum** | `*` | `#` | `X` | 8–14 | Purples/magenta |
| **Natural Caverns** | `.` | `%` | `+` | 8–14 | Grey/blue-white |

---

## Character Classes

All classes start with a **class-specific starter weapon** (not a Club) and a **Leather Cap** equipped. Starters are humble (mostly 1d4, +1 ATK) so floor 1 isn't a grind.

### Base Stats by Class

| Class | HP | Attack | Defense | MP | Starter weapon | Role |
|---|---|---|---|---|---|---|
| **Warrior** | 20 | 6 | 4 | 0 | Rusty Sword (1d4, +1) | Melee bruiser / tank |
| **Wizard** | 10 | 2 | 1 | 20 | Adept Staff (1d4, +1) | Fragile caster |
| **Thief** | 14 | 4 | 2 | 0 | Sneaky Dagger (1d4, +1, +10% backstab, throwable) | Skirmisher / utility |
| **Cleric** | 16 | 3 | 3 | 15 | Acolyte Mace (1d6, +1) | Sustain / undead hunter |

### Level-Up Gains (per level)

| Class | +HP | +ATK | +DEF | +MP |
|---|---|---|---|---|
| Warrior | 5 | 1 | 1 | — |
| Wizard | 3 | — | — | 5 |
| Thief | 4 | 1 | 1 | — |
| Cleric | 4 | — | 1 | 3 |

MP regenerates **1 per step** (movement tile). Leveling heals/restores by the gained amount and learns any newly-available spells.

### XP Curve (cumulative)

| Level | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|
| Total XP | 10 | 25 | 75 | 175 | 375 | 775 |

(Beyond L3 the step doubles: +50, +100, +200, +400 …)

---

## Class Abilities

### Warrior
- **Rage** (`R`, once per floor): damage ×2 for 3 turns (counts down per attack). Applies to each dual-wield strike.
- **Toughness** (passive): on each hit taken where damage > 1, 50% chance to absorb 1 point.
- **Dual Wield**: with a one-handed weapon in the main hand, a Warrior may equip a **second one-handed weapon** in the off-hand → **two attack rolls per turn**. A two-handed main weapon disables this.
- **Heavy gear access**: Warrior-only weapons (Maul, War Hammer, Great Sword, Halberd, Gorecleaver, Heavy Crossbow, Stormbolt Crossbow) and armor (Plate Mail, Great Helm, Kite Shield, Gauntlets).

### Wizard
- **Spellcasting** (`Z`): selects/casts a spell. In bump combat, **auto-casts the highest expected-damage spell it can afford** each round instead of using a weapon (skipped if silenced).
- Spells learned automatically at level thresholds (see Spells).

### Thief
- **Backstab** (passive): per hit, `level × 10% + weapon backstab bonus` chance to deal ×2 damage. (Some blades add flat backstab %.)
- **Envenom** (`E`, once per floor): coats blade — next **3 hits** apply Poison (3 turns, 2/tick).
- **Flee**: `min(50% + 5%/level, 100%)` vs 25% for other classes.
- **Trap detection** (passive): `level × 10%` (cap 100%) to detect traps within 20 tiles when opening a door.
- **Trap disarm** (`X`): `level × 10%` success on a detected trap.

### Cleric
- **Spellcasting** (`Z`): healing, buffs, Turn Undead, Purify, and holy damage.
- **Turn Undead**: destroys undead with `max_hp ≤ 10` outright; deals `randint(max_hp//2, max_hp-1)` to stronger undead.

---

## Combat

### Attack Resolution (now 1d10)
```
Roll 1d10 (natural)
  natural 1  → always miss
  natural 10 → always hit
  else hit if  natural + attacker ATK  >  defender DEF
Damage = weapon dice roll (unarmed = 1 static)
```
The natural-1/10 rule caps hit chance at 10%–90% — no build is ever fully immune or auto-hitting.

### Damage Mitigation Order (incoming hits)
1. **Warrior Toughness**: 50% chance −1 (only when raw damage > 1)
2. **Damage Reduction (DR)**: flat, summed from equipped armor/shields (a separate stat from DEF)
3. **Absorb pool**: finite pool from absorb spells (Shield, Divine Shield, Time Stop)
4. **Floor**: a landed hit always deals **at least 1** damage

### Damage Multipliers (player)
- Warrior Rage: ×2 (up to 3 turns)
- Thief Backstab: ×2 on proc
- Anti-undead weapons add their radiant bonus dice **after** the ×2 (the bonus itself is never doubled)
- Dual-wield Warrior: two independent attack + damage rolls

### Flee (`F`)
- Thief `min(50%+5%/level, 100%)`; others 25%. Success **freezes engaged monsters for 3 turns**. Failure gives the monster a free attack.

### Invulnerability
Scroll of Invulnerability: immune to all monster damage (melee + boss AoE) for 3 rounds, decremented per monster attack.

---

## Light & Field of View

| Source | Radius | Type | Notes |
|---|---|---|---|
| Base vision | 3 | Passive | Everyone |
| Torch (lit) | 12 | Off-hand | Consumed on unequip; **burnout**: 50% chance if >30 cumulative damage in one fight |
| Sunblade | 8 | Weapon | Unique; +1d8 vs undead |
| Aegis of Dawn | 8 | Off-hand/shield | Unique; +2 DEF, +1 DR |
| Starlit Helm | 10 | Helmet | Unique; +1 DEF, +1 DR |
| Scroll of Illumination | 18 | Read | Floor-wide ambient |
| Illumination spell | 15 | Cast | Wizard L2+, 4 MP, floor-wide |

---

## Weapons

Damage is `NdX`; ATK is the flat attack bonus added to the to-hit roll.

### Standard Weapons (all classes)

| Weapon | ATK | Damage | Value | Notes |
|---|---|---|---|---|
| Rusty Sword | +1 | 1d4 | 4 | Warrior starter |
| Adept Staff | +1 | 1d4 | 4 | Wizard starter |
| Sneaky Dagger | +1 | 1d4 | 4 | Thief starter; +10% backstab; throwable (5) |
| Acolyte Mace | +1 | 1d6 | 5 | Cleric starter |
| Dagger | +2 | 1d4 | 5 | Throwable (5) |
| Staff | +2 | 1d4 | 8 | |
| Mace | +2 | 1d6 | 12 | |
| Short Sword | +3 | 1d6 | 15 | |
| Broad Sword | +4 | 1d8 | 30 | |
| Long Sword | +4 | 1d10 | 40 | |
| Battle Axe | +5 | 2d6 | 60 | |

### Warrior-Only Heavy Weapons

| Weapon | ATK | Damage | Value | Notes |
|---|---|---|---|---|
| Maul | +4 | 3d6 | 60 | 2H |
| War Hammer | +5 | 2d8 | 70 | one-handed |
| Great Sword | +6 | 1d12 | 80 | 2H |
| Halberd | +7 | 2d10 | 100 | 2H |

### Ranged Weapons (ammo-based)

| Weapon | ATK | Damage | Value | Ammo | Notes |
|---|---|---|---|---|---|
| Sling | +1 | 1d4 | 10 | stone | |
| Hand Crossbow | +2 | 1d6 | 25 | bolt | |
| Shortbow | +2 | 1d6 | 25 | arrow | 2H |
| Longbow | +3 | 1d8 | 55 | arrow | 2H |
| Heavy Crossbow | +4 | 2d6 | 75 | bolt | 2H, Warrior-only |

Ammo: Pouch of Stones (8 gp, +20 stone), Quiver of Arrows (15 gp, +20 arrow), Case of Bolts (18 gp, +20 bolt). Default ranged range is 7 tiles (Chebyshev); thrown default 5.

### Unique / Named Weapons

| Weapon | ATK | Damage | Value | Notes |
|---|---|---|---|---|
| Fang | +3 | 1d6 | 120 | **3 strikes/turn**, +10% backstab, Thief-only |
| Flamebrand | +5 | 1d10 | 150 | fire flavor |
| Gorecleaver | +8 | 2d12 | 250 | 2H, Warrior-only |
| Sunblade | +4 | 1d8 | 180 | light 8; +1d8 vs undead |
| Wand of Sparks | +3 | 1d6 | 100 | ranged, self-powered, Wizard-only |
| Radiant Sling | +4 | 1d8 | 140 | ranged; +2d6 vs undead; Cleric-only |
| Whispering Bow | +5 | 1d8 | 180 | ranged, self-powered, Thief-only |
| Stormbolt Crossbow | +6 | 2d8 | 220 | 2H, ranged, self-powered, Warrior-only |

### Boss-Exclusive Unique Weapons (milestone drops)

| Weapon | ATK | Damage | Value | Notes |
|---|---|---|---|---|
| Quill of Unbinding | +4 | 1d8 | 140 | Wizard-only (Library boss) |
| Bonechoir Censer | +4 | 1d8 | 160 | +1d6 vs undead; Cleric-only (Catacombs boss) |
| Sigil-Carved Dagger | +4 | 1d6 | 150 | +15% backstab; Thief-only (Ritual boss) |

### Torch
Off-hand, light 12, 1 damage if swung, consumed on unequip, may burn out (50% after >30 dmg in one fight).

---

## Armor

**DEF** adds to the defender's target number; **DR** subtracts flat damage from each hit taken. Both matter now.

### Standard Armor (all classes)

| Item | Slot | DEF | DR | Other | Value |
|---|---|---|---|---|---|
| Leather Cap | Helmet | +1 | — | — | 4 |
| Iron Helm | Helmet | +1 | +1 | — | 15 |
| Leather Armor | Body | +1 | +1 | — | 10 |
| Chain Mail | Body | +2 | +1 | — | 30 |
| Small Shield | Off-hand | — | +1 | — | 8 |
| Tower Shield | Off-hand | +1 | +2 | — | 25 |
| Leather Boots | Boots | +1 | — | — | 20 |
| Iron Boots | Boots | +1 | +1 | — | 40 |
| Leather Gloves | Gloves | — | — | +1 ATK | 18 |
| Thief's Gloves | Gloves | — | — | +2 ATK | 60 |

### Warrior-Only Armor

| Item | Slot | DEF | DR | Other | Value |
|---|---|---|---|---|---|
| Great Helm | Helmet | +2 | +1 | — | 70 |
| Plate Mail | Body | +3 | +2 | — | 120 |
| Kite Shield | Off-hand | +1 | +2 | — | 80 |
| Gauntlets | Gloves | +1 | — | +1 ATK | 50 |

### Accessories

| Item | Slot | Effect | Value |
|---|---|---|---|
| Ring of Protection | Ring | +1 DEF | 50 |
| Ring of Clarity | Ring | +5 max MP | 60 |
| Amulet of Vitality | Amulet | +5 max HP | 60 |
| Boots of Speed | Boots | — (flavor, 0 DEF) | 45 |

### Unique / Magic-Light Items

| Item | Slot | Effect | Value |
|---|---|---|---|
| Starlit Helm | Helmet | +1 DEF, +1 DR, light 10 | 150 |
| Aegis of Dawn | Off-hand | +2 DEF, +1 DR, light 8 | 160 |

### Boss-Exclusive Unique Accessories (milestone drops)

| Item | Slot | Effect | Value |
|---|---|---|---|
| Dungeonheart Amulet | Amulet | +8 max HP, +5 max MP | 200 (Living Dungeon boss) |
| Warden's Manacle | Gloves | +2 DEF | 150 (Prison boss) |

---

## Potions (consumed with `P`)

| Potion | Effect | Value |
|---|---|---|
| Health Potion | +10 HP | 20 |
| Mana Potion | +10 MP | 20 |
| Potion of Knowledge | +10 XP (can level) | 35 |
| Antidote | Cures Poison | 15 |
| Elixir of Vitality | Full HP | 80 |
| Elixir of Clarity | Full MP | 80 |

---

## Scrolls (read with `C`)

| Scroll | Effect | Value |
|---|---|---|
| Scroll of Fireball | 3d6 to nearest monster | 40 |
| Scroll of Heal | +20 HP | 30 |
| Scroll of Invulnerability | Immune 3 turns | 60 |
| Scroll of Illumination | Floor light (radius 18) | 45 |

---

## Spells (`Z`)

Wizards auto-cast the best affordable **damage** spell when bump-attacking. Buff spells are cleared at the end of each combat; timed DEF buffs also tick down per turn. Absorb pools persist until spent or combat ends.

### Wizard Spells

| Spell | Lv | MP | Effect |
|---|---|---|---|
| Magic Bolt | 1 | 2 | 1d6 damage |
| Magic Armor | 1 | 3 | +2 DEF for 3 turns |
| Detect Magic | 1 | 2 | Reveal magical traps on floor |
| Blink | 1 | 5 | Teleport clear of monsters (~6 tiles, shortest safe hop) — escape melee, keep casting |
| Fireball | 2 | 5 | 1d10 **AoE**, point target, range 8, radius 2 |
| Illumination | 2 | 4 | Floor light (radius 15) |
| Lightning Bolt | 3 | 6 | 2d6 damage |
| Shield | 4 | 5 | **Absorb 15** |
| Meteor Swarm | 5 | 8 | 3d8 **AoE**, self-centered, radius 3 |
| Arcane Blast | 6 | 10 | 3d10 damage |
| Time Stop | 7 | 12 | **Absorb 25** |

### Cleric Spells

| Spell | Lv | MP | Effect |
|---|---|---|---|
| Heal | 1 | 4 | +2d6 HP |
| Smite | 1 | 3 | 1d8 holy damage |
| Bless | 1 | 3 | +1d6 ATK next combat |
| Sanctuary | 1 | 4 | +2 DEF for 3 turns |
| Purify | 2 | 3 | Remove one harmful status effect |
| Turn Undead | 2 | 5 | Destroy weak undead (≤10 HP); 50–99% dmg to strong |
| Light from Heaven | 3 | 6 | 2d8 holy damage |
| Greater Heal | 4 | 7 | +4d6 HP |
| Divine Shield | 5 | 6 | **Absorb 12** |
| Holy Fire | 6 | 9 | 3d10 holy damage |
| Wrath of Heaven | 7 | 10 | 4d8 holy damage |

> **Balance note:** AoE damage spells roll **independent** damage per target (not a split pool). Fireball/Meteor Swarm can hit clustered monsters + summoned boss adds hard.

---

## Status Effects

Applied by monsters on hit (chance-based), by traps, by Thief Envenom, and by boss AoE. Reapplying refreshes to the max duration/potency. Tick at start of the entity's turn.

| Effect | Behavior |
|---|---|
| **Poisoned** | `potency` damage/turn |
| **Burning** | `potency` fire damage/turn, **−1 DEF** while active |
| **Stunned** | Cannot move, attack, or cast |
| **Bound** | Cannot move (can still attack/cast) |
| **Silenced** | Cannot cast spells (hits Wizard/Cleric hardest) |

Cures: Antidote (poison), Cleric Purify (one effect, priority poison→burning→silenced→bound→stunned).

---

## Traps

Hidden until detected; trigger on step, then removed. `randint(2,5)` per floor. Thief-only detect/disarm.

| Trap | Damage | Effect | Magic? |
|---|---|---|---|
| Snap Trap | 1d4 | — | no |
| Floor Spikes | 1d8 | — | no |
| Crushing Rockfall | 1d10 | — | no |
| Flame Ward | 1d10 | Burning 2t/2 | yes |
| Poison Needle | 0 | Poisoned 5t/2 | no |
| Stun Trap | 1d4 | Stunned 1t | no |
| Web Trap | 0 | Bound 3t | no |
| Silence Trap | 0 | Silenced 4t | yes |

(Magic traps are the ones Detect Magic reveals.)

---

## Monsters

Counts: `min(6 + (floor-1)*2, 24)`. Stronger types weighted up with depth. Many now apply on-hit status effects.

### Regular Monsters

| Monster | Glyph | Floor | HP | ATK | DEF | XP | Undead | Weapon | AI | On-hit effect |
|---|---|---|---|---|---|---|---|---|---|---|
| Goblin | `g` | 1+ | 5 | 1 | 1 | 1 | — | — (club dmg) | Wander (chase 10) | — |
| Skeleton | `s` | 1+ | 8 | 2 | 1 | 2 | ☠ | Short Sword | Wander (7) | — |
| Orc | `o` | 2+ | 12 | 3 | 2 | 3 | — | Short Sword | Wander (8) | — |
| Zombie | `z` | 2+ | 15 | 4 | 2 | 4 | ☠ | — | Wander (5) | — |
| Bugbear | `b` | 2+ | 18 | 4 | 2 | 5 | — | Mace | Wander (9) | — |
| **Spider** | `s` | 2+ | 10 | 3 | 2 | 3 | — | bite | Wander (7) | Poison 30%, 4t/2 |
| Troll | `T` | 3+ | 25 | 5 | 3 | 7 | — | Broad Sword | Guard (6) | — |
| Mummy | `M` | 3+ | 20 | 5 | 4 | 8 | ☠ | claws | Wander (6) | — |
| Wight | `W` | 3+ | 18 | 6 | 3 | 9 | ☠ | Long Sword | Wander (8) | — |
| Owlbear | `O` | 4+ | 30 | 7 | 4 | 12 | — | claws | Guard (7) | Stun 20%, 1t |
| Wraith | `"` | 4+ | 22 | 7 | 5 | 14 | ☠ | claws | Wander (10) | Silence 15%, 3t |
| Umber Hulk | `U` | 5+ | 40 | 8 | 5 | 18 | — | claws | Guard (7) | Stun 25%, 1t |
| Vampire | `V` | 5+ | 35 | 9 | 6 | 22 | ☠ | claws | Wander (12) | — |
| Dragon | `D` | 7+ | 60 | 12 | 8 | 50 | — | claws/fire | Guard (10) | Burning 30%, 3t/3 |

**Undead (☠)** — vulnerable to Turn Undead and anti-undead weapons: Skeleton, Zombie, Mummy, Wight, Wraith, Vampire.

### Monster AI
- **Wander**: random (50% stay put each turn); switches to **Chase** within `chase_range` (Manhattan)
- **Guard**: returns to spawn beyond `guard_range`; chases within `chase_range`
- **Chase**: greedy step toward player; attacks when adjacent
- **Frozen**: after player flees, skips AI for 3 turns

### Loot (samples)
- Goblin/Skeleton: small gold, 10–15% common gear
- Troll: large gold, 30% weapon / 20% armor
- Wraith: Gem + 25% accessory
- Vampire: Gem + large gold, 40% accessory, 25% rare weapon
- Dragon: 2× large gold + Gem + guaranteed rare item, 50% accessory, 30% elixir
- **Floor-1 guarantee**: the first monster on floor 1 always carries a Torch.

---

## Bosses (floors 3, 5, 10)

One boss guards the down-stair on milestone floors, chosen by theme. **Lesser** (F3 mini-boss) and **Greater** (F5) per theme; F10 reuses the Greater form scaled by `scale_boss` (HP ×2, ATK ×1.5, XP ×2, earlier phase at 60%, faster cooldowns, +2 summon cap).

Boss toolkit: **phase change** (at ≤50% HP: ATK ×1.3, cooldowns reset), **summon** adds on a cooldown up to a lifetime cap, and **AoE blast** (auto-hits, but DR/absorb still apply) on a cooldown. Abilities only fire once engaged (within chase range).

### Floor 3 — Lesser bosses

| Boss (theme) | HP | ATK | DEF | XP | On-hit | AoE | Summons | Drop |
|---|---|---|---|---|---|---|---|---|
| Ink Wraith (Library) | 45 | 8 | 4 | 30 | Silence 30% | 2d4 r3, silence | — | Quill of Unbinding |
| Gnashing Maw (Living) | 50 | 9 | 3 | 32 | Poison 30% | 2d6 r2 | — | Dungeonheart Amulet |
| Warden's Shade (Prison) | 48 | 9 | 4 | 31 | Bound 25% | 2d5 r2, bound | — | Warden's Manacle |
| Bone Choir (Catacombs) | 46 | 8 | 4 | 30 | — | — | Skeletons (max 4) | Bonechoir Censer |
| Acolyte of the Sigil (Ritual) | 44 | 9 | 3 | 30 | Burning 30% | 2d5 r3, burning | — | Sigil-Carved Dagger |
| Broodmother (Caverns) | 47 | 8 | 4 | 31 | Poison 35% | — | Spiders (max 4) | Aegis of Dawn |

All Lesser bosses also drop a Cracked Rune Fragment + Large Gold Pile.

### Floor 5 — Greater bosses (phase at 50%, summon max 6)

| Boss (theme) | HP | ATK | DEF | XP | On-hit | AoE | Summons | Drop |
|---|---|---|---|---|---|---|---|---|
| The Unbound Index (Library) | 90 | 12 | 6 | 70 | Silence 30% | 2d5 r3, silence | Skeletons | Quill of Unbinding |
| Heart of the Dungeon (Living) | 100 | 13 | 5 | 75 | Poison 30% | 3d6 r2 | Zombies | Dungeonheart Amulet |
| Broken-Chain Colossus (Prison) | 95 | 13 | 6 | 72 | Bound 25% | 2d6 r2, bound | Skeletons | Warden's Manacle |
| The Lich Cantor (Catacombs) | 88 | 12 | 6 | 70 | Poison 25% | 2d6 r3, poison | Skeletons | Bonechoir Censer |
| The Sigil Incarnate (Ritual) | 92 | 13 | 6 | 74 | Burning 30% | 3d6 r3, burning | Zombies | Sigil-Carved Dagger + Flamebrand |
| The Stone Tyrant (Caverns) | 98 | 14 | 7 | 76 | Poison 30% | 3d6 r2 | Spiders | Aegis of Dawn |

Greater bosses add a Gem to their drop (except the Sigil Incarnate, which drops Flamebrand instead). Floor-10 forms roughly double the HP and XP and hit ~50% harder.

---

## Treasure (auto-converted on pickup)

| Item | Gold | Other |
|---|---|---|
| Gold Coins | 5 | — |
| Gold Pile | 15 | — |
| Large Gold Pile | 30 | — |
| Gem | 50 | — |
| Ornate Rug | 15 | — |
| Silver Candlestick | 20 | — |
| Ink Vial | 35 | — |
| Ancient Tome | 40 | — |
| Idol | 60 | — |
| Cracked Rune Fragment | 0 | +5 XP |
| Blessed Chalice | 15 | +5 HP |

---

## Shop

Appears in the largest eligible room. Stock scales with floor. Weapons and ammo are available from **floor 1** now (so no class is stuck on its starter). Prices = item gold value.

| Floor | Adds |
|---|---|
| 1+ | Health/Mana Potion, Antidote, Torch, Scroll of Illumination, Dagger, Staff, Mace, Short Sword, Sling, Pouch of Stones, Quiver of Arrows, Case of Bolts |
| 2+ | Elixir of Vitality, Elixir of Clarity, Hand Crossbow, Shortbow |
| 3+ | Broad Sword, Wand of Sparks |
| 4+ | Leather Armor, Small Shield, Iron Helm, Leather Boots, Leather Gloves, Longbow, Radiant Sling |
| 5+ | Long Sword, Ring of Protection, Heavy Crossbow, Whispering Bow |
| 6+ | Chain Mail, Scroll of Heal, Scroll of Invulnerability, Iron Boots, Gauntlets, Stormbolt Crossbow |
| 7+ | Battle Axe, Scroll of Fireball, Boots of Speed, Thief's Gloves |

---

## Death Screen

Shows name, class, floor, and final stats (level, XP, gold, floors descended, squares traveled, monsters killed, damage taken, items found, MP spent) plus the **last 5 log entries** in red. `Q` quit, `R` restart.

---

## What Does Not Yet Exist (planned)

- **Glyph system** — the signature mechanic: collectible runes (Reveal, Bind, Break, Move, Light, Name, Rewrite, Seal) and glyph-themed enemies (Ink Wraith etc. currently exist only as bosses). Should feel useful to all four classes, differently.
- **Save / load** (permadeath only)
- **FOV persistence between floors**
- **Secret rooms / hidden passages**
- **Item identification** (unidentified potions/scrolls)
- **True-name mechanics**

---

## Balancing Questions to Investigate

These follow directly from the numbers above — flagged for review, not yet decided:

1. **Wizard early game.** 10 HP, 2 ATK, 1 DEF, and a 1d4 starter. Magic Bolt (1d6, 2 MP) with 20 MP + 1/step regen — does the Wizard survive floors 1–2 before Fireball (L2)?
2. **DEF vs the 1d10 curve.** With natural-10 auto-hits, high-ATK monsters (Dragon +12, Greater bosses +12–14) beat almost any DEF. Is DR now the *real* defensive stat, and do casters/thieves have enough DR access (mostly Warrior-gated)?
3. **Cleric identity.** Turn Undead is strong vs undead-heavy themes (Catacombs, Library) but dead weight elsewhere. Is the Cleric's non-undead floor experience compelling?
4. **Thief scaling.** Backstab ×2 scales with level; Fang (3 strikes, +10% backstab each) + Envenom is a burst spike. Is late-Thief overpowered vs bosses, or still too fragile at 14 base HP?
5. **Warrior dominance.** Exclusive access to heavy weapons **and** the highest-DR armor **and** Toughness **and** Rage. Are the other three classes' unique tools (spells, backstab, utility) worth the survivability gap?
6. **Boss AoE + summons.** Auto-hit AoE plus summoned adds punish melee positioning; independent-roll AoE spells reward Wizards. Are F5 Greater bosses (88–100 HP) fair for a melee class arriving underleveled?
7. **Ranged access by class.** Every class has a self-powered unique ranged option, but ammo weapons need shop trips. Does ranged trivialize Guard-AI monsters (Troll, Owlbear, Umber Hulk, Dragon) that won't leave their post?
8. **Gold economy.** Boss uniques are free drops; is the shop still a meaningful sink by floor 5+, and are elixirs/scrolls priced to matter?
