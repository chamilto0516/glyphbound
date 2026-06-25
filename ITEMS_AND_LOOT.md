# Items & Loot System Expansion

## Overview
Expanded the item catalog from 13 items to 30+ items, added monster loot drops, new equipment slots (ring, amulet), and improved loot distribution.

---

## New Items Added

### **Weapons** (5 new + 2 unique)
| Item | ATK | Damage | Gold | Notes |
|------|-----|--------|------|-------|
| Mace | +2 | 1d6 | 12 gp | Cleric weapon |
| Long Sword | +4 | 1d10 | 40 gp | Upgrade from Short Sword |
| Battle Axe | +5 | 2d6 | 60 gp | Top-tier weapon |
| **Fang** | +3 | 1d6 | 80 gp | Unique dagger |
| **Flamebrand** | +5 | 1d10 | 150 gp | Unique fire sword |

### **Armor** (3 new)
| Item | Slot | DEF | Gold |
|------|------|-----|------|
| Chain Mail | Armor | +3 | 30 gp |
| Iron Helm | Helmet | +2 | 15 gp |
| Tower Shield | Shield | +3 | 25 gp |

### **Accessories** (NEW SLOTS: Ring, Amulet)
| Item | Slot | Effect | Gold |
|------|------|--------|------|
| Ring of Protection | Ring | +1 DEF | 50 gp |
| Amulet of Vitality | Amulet | +5 max HP | 60 gp |
| Ring of Clarity | Ring | +5 max MP | 60 gp |

### **Scrolls** (NEW KIND - not yet functional)
| Item | Effect | Gold |
|------|--------|------|
| Scroll of Fireball | One-use 1d10 damage spell | 40 gp |
| Scroll of Heal | One-use 2d6 HP restore | 30 gp |
| Scroll of Teleport | One-use random floor teleport | 50 gp |

### **Gold Coins** (NEW - monster drops)
| Item | Value |
|------|-------|
| Gold Coins | 5 gp |
| Gold Pile | 15 gp |
| Large Gold Pile | 30 gp |

---

## Monster Loot Drops

### **Loot Tables**

| Monster | Guaranteed | Chance Drops |
|---------|-----------|--------------|
| **Goblin** | 5 gp | 10% weapon |
| **Skeleton** | 5 gp | 15% weapon or armor |
| **Orc** | 15 gp | 20% weapon, 10% potion |
| **Zombie** | 5 gp | 20% potion |
| **Troll** | 30 gp | 30% weapon, 20% armor |

### **Mechanics**
- Loot generated on monster death via `Monster.drop_loot()`
- Placed on ground at monster's position
- Player picks up with 'G' key
- Loot announced in combat log

---

## Floor Loot Distribution

### **Quantity**
- Base: 3-6 items per floor
- Scales with depth: +1 item every 2 floors (max +3)
- Floor 10: 6-9 items

### **Rarity Tiers**

**Common (60%):**
- 35% Potions (Health, Mana)
- 15% Treasure (Gem, Torch, Rug)
- 10% Scrolls

**Uncommon (30%):**
- 15% Common Weapons (Club, Dagger, Short Sword, Staff, Mace)
- 15% Common Armor (Leather Cap, Leather Armor, Small Shield)

**Rare (8%) — Floor 3+:**
- 4% Rare Weapons (Broad Sword, Long Sword, Battle Axe)
- 4% Rare Armor (Chain Mail, Iron Helm, Tower Shield)

**Very Rare (2%):**
- 1% Accessories (Ring, Amulet) — Floor 5+
- 1% Unique Weapons (Fang, Flamebrand) — Floor 7+

---

## Equipment Slots

### **New Slots**
- **Ring**: +DEF or +MP bonuses
- **Amulet**: +HP bonuses

### **All Slots**
1. Weapon
2. Armor (body)
3. Helmet
4. Shield
5. Ring
6. Amulet

### **Status Panel Display**
```
W: Flamebrand      H: Iron Helm
A: Chain Mail      S: Tower Shield
R: Ring of Clarity N: Amulet of Vitality
```

---

## New Item Properties

### **`is_unique`** (bool)
- Marks special/named items (Fang, Flamebrand)
- Can be used for:
  - Special visual effects
  - One-per-game restrictions
  - Quest item mechanics

### **`hp_bonus` / `mp_bonus` Behavior**
- **Potions**: Restore HP/MP when consumed
- **Accessories**: Permanently increase max HP/MP when equipped

### **Max HP/MP Calculation**
```python
effective_max_hp = base_max_hp + equipped_hp_bonuses
effective_max_mp = base_max_mp + equipped_mp_bonuses
```

---

## Loot Pools (items.py exports)

```python
COMMON_WEAPONS = [ITEM_CLUB, ITEM_DAGGER, ...]
RARE_WEAPONS = [ITEM_BROAD_SWORD, ITEM_LONG_SWORD, ...]
UNIQUE_WEAPONS = [ITEM_FANG, ITEM_FLAMEBRAND]

COMMON_ARMOR = [ITEM_LEATHER_CAP, ...]
RARE_ARMOR = [ITEM_CHAIN_MAIL, ...]

ACCESSORIES = [ITEM_RING_OF_PROTECTION, ...]
POTIONS = [ITEM_HEALTH_POTION, ITEM_MANA_POTION]
SCROLLS = [ITEM_SCROLL_FIREBALL, ...]
TREASURE = [ITEM_GEM, ITEM_TORCH, ITEM_RUG]
GOLD = [ITEM_GOLD_PILE_SMALL, ...]
```

---

## Combat Integration

### **Loot Drop Flow**
1. Monster dies in combat
2. `monster.drop_loot()` generates random items
3. Items announced in combat log: "Goblin dropped: Gold Coins, Dagger"
4. `CombatResult` includes `loot` list
5. App places loot on ground at monster position
6. Player picks up with 'G' key

### **Combat Functions Return Loot**
```python
resolve_combat(player, monster) -> (log, survived, loot)
apply_spell_to_monster(player, spell, monster) -> (log, killed, loot)
```

---

## Item Catalog Summary

### **Total Items: 30+**

| Category | Count | Notes |
|----------|-------|-------|
| Weapons | 10 | 7 common, 3 unique (Fang, Flamebrand) + 2 named |
| Armor | 6 | Leather, Chain, Helms, Shields |
| Accessories | 3 | Rings, Amulets (new slots) |
| Potions | 4 | Health, Mana, Elixirs |
| Scrolls | 3 | Placeholder (not functional yet) |
| Treasure | 6 | Gem, Torch, Rug, Gold piles |

---

## Future Enhancements

### **Scroll Implementation**
- Use scrolls from inventory
- One-time spell cast for any class
- Consume on use

### **Item Identification**
- Unknown scrolls/potions
- Identify via use or spell

### **Cursed Items**
- Can't unequip until uncursed
- Negative stat effects

### **Item Enchantments**
- +1/+2/+3 weapons and armor
- Random prefix/suffix modifiers

### **Crafting/Upgrading**
- Combine items
- Upgrade at blacksmith

### **Quest Items**
- Special items required for progression
- Keys, runes, seals

---

## Testing

```bash
# Test monster loot generation
python -c "
from glyphbound.monsters import spawn_goblin, spawn_troll
for i in range(5):
    g = spawn_goblin()
    print(f'Goblin {i+1}:', [item.name for item in g.drop_loot()])
    t = spawn_troll()
    print(f'Troll {i+1}:', [item.name for item in t.drop_loot()])
"
```

---

## Balance Notes

- **Early game (1-3)**: Common weapons/armor, frequent potions
- **Mid game (4-6)**: Rare equipment starts appearing, accessories at floor 5
- **Late game (7+)**: Unique weapons, full accessory set possible
- **Troll farming**: Best early gold source (30 gp guaranteed)
- **Orc farming**: Good weapon/potion source (20% weapon drop)
