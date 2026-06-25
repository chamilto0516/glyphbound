#!/usr/bin/env python3
"""Quick test of level-up system"""

from glyphbound.player import Player, CharacterClass, xp_for_level

# Test XP thresholds
print("XP Thresholds:")
for level in range(1, 8):
    print(f"  Level {level}: {xp_for_level(level)} XP")

print("\n" + "="*50 + "\n")

# Test Warrior level-up
warrior = Player(name="TestWarrior", char_class=CharacterClass.WARRIOR)
print(f"Warrior Initial: Lv{warrior.level} HP:{warrior.hp}/{warrior.max_hp} ATK:{warrior.attack} DEF:{warrior.defense}")

# Give enough XP to reach level 3
warrior.xp = 25
leveled, msgs = warrior.check_level_up()
print(f"\nAfter gaining 25 XP:")
print(f"  Leveled up: {leveled}")
for msg in msgs:
    print(f"  {msg}")
print(f"  Stats: Lv{warrior.level} HP:{warrior.hp}/{warrior.max_hp} ATK:{warrior.attack} DEF:{warrior.defense}")
print(f"  XP: {warrior.xp} (next level: {warrior.xp_to_next_level})")

print("\n" + "="*50 + "\n")

# Test Wizard level-up
wizard = Player(name="TestWizard", char_class=CharacterClass.WIZARD)
print(f"Wizard Initial: Lv{wizard.level} HP:{wizard.hp}/{wizard.max_hp} MP:{wizard.mp}/{wizard.max_mp}")

wizard.xp = 10  # Level 2
leveled, msgs = wizard.check_level_up()
print(f"\nAfter gaining 10 XP:")
print(f"  Leveled up: {leveled}")
for msg in msgs:
    print(f"  {msg}")
print(f"  Stats: Lv{wizard.level} HP:{wizard.hp}/{wizard.max_hp} MP:{wizard.mp}/{wizard.max_mp}")
print(f"  XP: {wizard.xp} (next level: {wizard.xp_to_next_level})")
