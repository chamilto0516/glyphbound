#!/usr/bin/env python3
"""Test monster AI behavior"""

from glyphbound.dungeon import generate_dungeon, FLOOR
from glyphbound.ai import ai_turn, manhattan_distance
from glyphbound.themes import ALL_THEMES

# Generate a test dungeon
dungeon = generate_dungeon(seed=42, theme=ALL_THEMES[0], floor=1)
print(f"Generated dungeon with {len(dungeon.monsters)} monsters")
print(f"Player at: ({dungeon.party_x}, {dungeon.party_y})")
print()

# Test each monster's AI
for (mx, my), monster in list(dungeon.monsters.items()):
    dist = manhattan_distance(mx, my, dungeon.party_x, dungeon.party_y)
    print(f"{monster.name} at ({mx}, {my})")
    print(f"  Distance to player: {dist}")
    print(f"  AI state: {monster.ai_state.value}")
    print(f"  Chase range: {monster.chase_range}")

    # Simulate one AI turn
    new_pos = ai_turn(dungeon, monster, mx, my)
    if new_pos:
        new_x, new_y = new_pos
        print(f"  → Would move to ({new_x}, {new_y})")
        if (new_x, new_y) == (dungeon.party_x, dungeon.party_y):
            print(f"    (ATTACK PLAYER!)")
        new_dist = manhattan_distance(new_x, new_y, dungeon.party_x, dungeon.party_y)
        if new_dist < dist:
            print(f"    (moving closer: {dist} → {new_dist})")
        elif new_dist > dist:
            print(f"    (moving away: {dist} → {new_dist})")
    else:
        print(f"  → Stays put")
    print()

print("✅ AI test complete")
