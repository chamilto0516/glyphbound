#!/usr/bin/env python3
"""Test that characters start with gear equipped"""

from glyphbound.player import Player, CharacterClass
from glyphbound.items import EquipSlot

print("Testing starting gear...\n")

for char_class in [CharacterClass.WARRIOR, CharacterClass.WIZARD, CharacterClass.THIEF, CharacterClass.CLERIC]:
    player = Player(name="Test", char_class=char_class)

    print(f"{char_class.value}:")
    print(f"  HP: {player.hp}/{player.max_hp}  ATK: {player.attack}  DEF: {player.defense}")

    weapon = player.equipped.get(EquipSlot.WEAPON.value)
    helmet = player.equipped.get(EquipSlot.HELMET.value)

    print(f"  Weapon: {weapon.name if weapon else 'None'}")
    print(f"  Helmet: {helmet.name if helmet else 'None'}")
    print(f"  Inventory: {len(player.inventory)} items")
    print()

print("✅ Starting gear test complete")
