#!/usr/bin/env python3
"""Test spell progression system"""

from glyphbound.player import Player, CharacterClass
from glyphbound.spells import WIZARD_SPELLS, CLERIC_SPELLS

print("="*60)
print("WIZARD SPELL PROGRESSION")
print("="*60)

wizard = Player(name="TestWizard", char_class=CharacterClass.WIZARD)

for level in range(1, 8):
    wizard.level = level
    wizard.xp = 0
    wizard._learn_spells_for_level()

    print(f"\nLevel {level}: {len(wizard.spells)} spells available")
    for spell in wizard.spells:
        print(f"  • {spell.name:20} — {spell.mp_cost} MP, {spell.damage_label():15} {spell.description}")

print("\n" + "="*60)
print("CLERIC SPELL PROGRESSION")
print("="*60)

cleric = Player(name="TestCleric", char_class=CharacterClass.CLERIC)

for level in range(1, 8):
    cleric.level = level
    cleric.xp = 0
    cleric._learn_spells_for_level()

    print(f"\nLevel {level}: {len(cleric.spells)} spells available")
    for spell in cleric.spells:
        print(f"  • {spell.name:20} — {spell.mp_cost} MP, {spell.damage_label():15} {spell.description}")

print("\n" + "="*60)
print("LEVEL UP SPELL LEARNING TEST")
print("="*60)

test_wiz = Player(name="LevelUpWiz", char_class=CharacterClass.WIZARD)
print(f"\nStarting spells (level 1): {len(test_wiz.spells)}")
for s in test_wiz.spells:
    print(f"  • {s.name}")

# Give enough XP to reach level 3
test_wiz.xp = 25
leveled, msgs = test_wiz.check_level_up()

print(f"\nAfter leveling to {test_wiz.level}:")
for msg in msgs:
    print(f"  {msg}")

print(f"\nTotal spells: {len(test_wiz.spells)}")
for s in test_wiz.spells:
    print(f"  • {s.name} (requires level {s.min_level})")

print("\n✅ Spell progression test complete")
