from __future__ import annotations
from models.items import Item, Consumable
from models.enums import EquipSlot
from core.inventory import Inventory
from core.equipment import Equipment


class Character:
    """Центральний координатор — делегує логіку Inventory та Equipment."""

    def __init__(self, name: str, max_hp: int = 120):
        self.name      = name
        self.max_hp    = max_hp
        self.hp        = max_hp
        self.inventory = Inventory()
        self.equipment = Equipment()

    def heal(self, amount: int) -> None:
        self.hp = min(self.hp + amount, self.max_hp)

    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - amount)

    def pick_up(self, item: Item) -> bool:
        return self.inventory.add_item(item)

    def equip_item(self, item: Item, slot: EquipSlot) -> tuple[bool, str]:
        if item not in self.inventory.items:
            return False, f"«{item.name}» не в інвентарі"
        ok, old = self.equipment.equip(item, slot)
        if not ok:
            return False, f"«{item.name}» не підходить до слоту {slot.value}"
        if old:
            self.inventory.add_item(old)
        return True, f"Екіпіровано «{item.name}» → {slot.value}"

    def unequip_item(self, slot: EquipSlot) -> tuple[bool, str]:
        item = self.equipment.unequip(slot)
        if not item:
            return False, "Слот порожній"
        self.inventory.add_item(item)
        return True, f"Знято «{item.name}»"

    def use_item(self, item: Item) -> str:
        if item not in self.inventory.items:
            return f"«{item.name}» не знайдено"
        msg = item.use(self)
        if isinstance(item, Consumable):
            self.inventory.remove_item(item)
        return msg
