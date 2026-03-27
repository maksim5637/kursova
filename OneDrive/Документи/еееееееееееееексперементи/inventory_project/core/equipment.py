from __future__ import annotations
from typing import Optional
from models.items import Item, Weapon, Armor
from models.enums import EquipSlot


class Equipment:
    """Клас спорядження — Strategy Pattern."""

    def __init__(self):
        self._slots: dict[EquipSlot, Optional[Item]] = {
            EquipSlot.WEAPON: None,
            EquipSlot.HEAD:   None,
            EquipSlot.BODY:   None,
            EquipSlot.LEGS:   None,
        }

    def _compatible(self, item: Item, slot: EquipSlot) -> bool:
        """Strategy: кожен тип перевіряє свою сумісність."""
        if isinstance(item, Weapon):
            return slot == EquipSlot.WEAPON
        if isinstance(item, Armor):
            return item.slot == slot
        return False

    def equip(self, item: Item, slot: EquipSlot) -> tuple[bool, Optional[Item]]:
        if not self._compatible(item, slot):
            return False, None
        old = self._slots[slot]
        self._slots[slot] = item
        return True, old

    def unequip(self, slot: EquipSlot) -> Optional[Item]:
        item = self._slots.get(slot)
        self._slots[slot] = None
        return item

    def get_item(self, slot: EquipSlot) -> Optional[Item]:
        return self._slots.get(slot)

    def get_defense_bonus(self) -> int:
        return sum(
            i.defense for i in self._slots.values()
            if isinstance(i, Armor)
        )

    def get_attack_bonus(self) -> int:
        return sum(
            i.damage for i in self._slots.values()
            if isinstance(i, Weapon)
        )
