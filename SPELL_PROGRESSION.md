# Spell Progression System

## Overview
Wizards and Clerics now learn new spells as they level up, starting with 4 spells at level 1 and gaining 1 additional spell per level thereafter (10 total spells by level 7).

## Wizard Spells (10 total)

| Level | Spell Name | MP Cost | Effect | Description |
|-------|------------|---------|--------|-------------|
| 1 | **Magic Bolt** | 2 | 1d6 damage | Basic arcane attack |
| 1 | **Magic Armor** | 3 | +1d10 DEF | Defense buff for next combat |
| 1 | **Detect Magic** | 2 | Reveal | Shows hidden items/monsters (not yet implemented) |
| 1 | **Blink** | 4 | Teleport | Short-range escape (not yet implemented) |
| 2 | **Fireball** | 5 | 1d10 damage | Fire attack |
| 3 | **Lightning Bolt** | 6 | 2d6 damage | Electric attack |
| 4 | **Shield** | 5 | +2d10 DEF | Stronger defense buff |
| 5 | **Meteor Swarm** | 8 | 3d8 damage | Massive fire attack |
| 6 | **Arcane Blast** | 10 | 3d10 damage | Pure magical destruction |
| 7 | **Time Stop** | 12 | +2d20 DEF | Ultimate defense buff |

### Wizard Strategy
- **Early game (1-2)**: Rely on Magic Bolt for damage, Magic Armor for defense
- **Mid game (3-5)**: Unlock stronger damage spells (Lightning, Meteor)
- **Late game (6-7)**: Access ultimate spells (Arcane Blast, Time Stop)

---

## Cleric Spells (10 total)

| Level | Spell Name | MP Cost | Effect | Description |
|-------|------------|---------|--------|-------------|
| 1 | **Heal** | 4 | Restore 2d6 HP | Basic healing |
| 1 | **Smite** | 3 | 1d8 damage | Holy attack |
| 1 | **Bless** | 3 | +1d6 ATK | Attack buff for next combat |
| 1 | **Sanctuary** | 4 | +1d8 DEF | Defense buff for next combat |
| 2 | **Turn Undead** | 5 | Destroy/damage undead | Anti-undead specialty |
| 3 | **Light from Heaven** | 6 | 2d8 damage | Stronger holy attack |
| 4 | **Greater Heal** | 7 | Restore 4d6 HP | Powerful healing |
| 5 | **Divine Shield** | 6 | +2d10 DEF | Stronger defense buff |
| 6 | **Holy Fire** | 9 | 3d10 damage | Massive holy attack |
| 7 | **Wrath of Heaven** | 10 | 4d8 damage | Ultimate holy judgment |

### Cleric Strategy
- **Early game (1-2)**: Balance healing, buffs, and attacks; Turn Undead at level 2
- **Mid game (3-5)**: Stronger healing and damage options
- **Late game (6-7)**: Ultimate offensive and defensive spells

---

## Implementation Details

### New Spell Effects
- **BUFF_ATK**: Increases attack for next combat (Bless)
- **DETECT**: Reveals items/monsters (placeholder for future)
- **BLINK**: Short-range teleport (placeholder for future)

### Spell Dataclass
```python
@dataclass
class Spell:
    name: str
    mp_cost: int
    effect: SpellEffect
    min_level: int    # NEW: minimum level required to learn
    # ... damage/buff dice fields
```

### Learning Mechanics
- **At character creation**: Learn all spells with `min_level <= 1` (4 spells)
- **At level up**: Automatically learn all spells with `min_level <= current_level`
- **No spell selection**: Spells are granted automatically (could add choice system later)

### Player Changes
- Added `temp_attack_bonus` field (like `temp_defense_bonus`)
- Attack property now includes `temp_attack_bonus`
- `_learn_spells_for_level()` filters spell list by level requirement
- `check_level_up()` calls `_learn_spells_for_level()` and logs new spells

### Combat Integration
- Temp attack/defense bonuses cleared after combat (both classes)
- Bless spell applies temp attack bonus
- Sanctuary/Divine Shield apply temp defense bonus
- All buffs expire after combat ends

---

## Level-Up Experience

When a Wizard levels up from 2 to 3:
```
LEVEL UP! You are now level 3!
  +3 HP  +5 MP
  Learned spell: Lightning Bolt
```

When a Cleric levels up from 1 to 2:
```
LEVEL UP! You are now level 2!
  +4 HP  +3 MP
  Learned spell: Turn Undead
```

---

## Progression Curve

### Wizard MP Scaling
- Level 1: 20 MP (can cast Magic Bolt 10×, Fireball 4×)
- Level 2: 25 MP (unlocks Fireball)
- Level 3: 30 MP (unlocks Lightning Bolt)
- Level 5: 40 MP (can cast Meteor Swarm 5×)
- Level 7: 50 MP (can cast Time Stop 4× or Arcane Blast 5×)

### Cleric MP Scaling
- Level 1: 15 MP (can cast Heal 3×, Smite 5×)
- Level 2: 18 MP (unlocks Turn Undead)
- Level 4: 24 MP (unlocks Greater Heal, can cast 3×)
- Level 7: 33 MP (can cast Wrath of Heaven 3×, Holy Fire 3×)

---

## Future Enhancements

### Spell Selection System
Instead of auto-learning, let player choose 1 spell from a pool at each level:
- More player agency
- Builds specialization (offense vs defense vs utility)
- Replayability

### Spell Upgrades
Let players upgrade existing spells instead of learning new ones:
- Magic Bolt → Lightning Bolt → Arcane Blast
- Heal → Greater Heal → Mass Heal

### Spell Combinations
- Cast 2+ spells in one turn for combo effects
- Example: Magic Armor + Blink = defensive escape

### Spell Scrolls
- Non-casters can use scrolls found in dungeon
- Limited-use items for any class

---

## Testing

Run `python test_spells.py` to verify:
- Spell lists for each class
- Level-based spell availability
- Level-up spell learning messages
