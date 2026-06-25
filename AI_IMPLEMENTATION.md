# Monster AI Implementation

## Overview
Monsters now move autonomously on the map using turn-based AI with different behavior patterns.

## Key Features

### 1. AI States (glyphbound/monsters.py)
- **WANDER**: Random movement, 50% chance to stay put
- **CHASE**: Pursue player when within chase range
- **GUARD**: Stay near spawn point, return if wandering too far

### 2. Monster Properties
Each monster has:
- `ai_state`: Current behavior mode
- `spawn_x`, `spawn_y`: Original spawn location (for guards)
- `chase_range`: Distance at which they detect and pursue player
- `guard_range`: Max distance guards roam from spawn

### 3. Monster Personalities
| Monster  | AI State | Chase Range | Behavior |
|----------|----------|-------------|----------|
| Goblin   | WANDER   | 10 tiles    | Aggressive, chases from far |
| Skeleton | WANDER   | 7 tiles     | Standard pursuit |
| Orc      | WANDER   | 8 tiles     | Standard pursuit |
| Zombie   | WANDER   | 5 tiles     | Slow, won't chase far |
| Troll    | GUARD    | 6 tiles, guard 8 | Territorial, stays near spawn |

### 4. Pathfinding (glyphbound/ai.py)
- **Simple greedy chase**: Move toward target by reducing Manhattan distance
- **4-directional movement**: North, South, East, West (no diagonals)
- **Collision avoidance**: Won't walk into walls, other monsters, or player
- **Attack detection**: Stops adjacent to player (triggers combat)

### 5. Turn System (glyphbound/app.py)
**Player Turn:**
1. Player moves (arrow keys)
2. Player action completes
3. → **All monsters take turns**
4. Monsters that bump player trigger attacks
5. UI refreshes

**Monster Turn:**
- Each monster evaluates AI state
- If player within chase range → move toward player
- If adjacent to player → attack (no movement)
- Otherwise → wander or guard behavior

### 6. Combat Integration
**Bump Combat:**
- Monster moves into player space → monster attacks player
- Attack resolves immediately (damage, HP loss, death check)
- No combat screen for monster-initiated attacks (keeps movement fluid)

**Player-Initiated Combat:**
- Player moves into monster space → opens combat screen (unchanged)
- Turn-based combat with full options (attack, spell, potion, flee)

## Technical Details

### New Files
- **glyphbound/ai.py**: AI behavior logic and pathfinding

### Modified Files
- **glyphbound/monsters.py**: Added AI state, chase/guard ranges
- **glyphbound/dungeon.py**: Added `move_monster()` method, set spawn positions
- **glyphbound/app.py**: Added `_monster_turns()`, `_monster_attacks_player()`

### AI Algorithm
```python
def ai_turn(dungeon, monster, mx, my):
    dist_to_player = manhattan_distance(mx, my, player_x, player_y)
    
    # CHASE if player nearby
    if dist_to_player <= chase_range:
        if dist_to_player == 1:
            return None  # attack (handled by caller)
        else:
            return move_toward(player)
    
    # GUARD if too far from spawn
    if ai_state == GUARD and dist_from_spawn > guard_range:
        return move_toward(spawn)
    
    # WANDER randomly (50% chance)
    if random() < 0.5:
        return random_neighbor()
```

## Gameplay Impact

### Before AI:
- Static spawn points
- Predictable, safe exploration
- No time pressure
- Combat only when you choose

### After AI:
- **Dynamic threats**: Monsters patrol and chase
- **Tactical positioning**: Can't rest in corridors near monsters
- **Retreat mechanics**: Low HP? Run away before monster catches you
- **Ambush risk**: Wandering into a monster's chase range triggers pursuit
- **Time pressure**: Can't stand still indefinitely near enemies

## Testing
Run `python test_ai.py` to verify AI behavior without launching the full game.

## Future Enhancements
- [ ] Diagonal movement (8-directional)
- [ ] A* pathfinding for smarter pursuit
- [ ] Group behavior (pack tactics, flee when outnumbered)
- [ ] Monster fleeing at low HP
- [ ] Ranged monsters (archers, spellcasters)
- [ ] Monster sleep/patrol patterns
- [ ] Noise/scent tracking
