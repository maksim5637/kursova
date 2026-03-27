from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from models.enums import ItemType, EquipSlot

if TYPE_CHECKING:
    from core.character import Character


class Item(ABC):
    """Базовий клас предмета — Factory Method."""

    def __init__(self, name: str, weight: float,
                 grid_w: int, grid_h: int, item_type: ItemType):
        self.name        = name
        self.weight      = weight
        self.grid_width  = grid_w
        self.grid_height = grid_h
        self.item_type   = item_type
        self.grid_x: int = -1
        self.grid_y: int = -1

    @abstractmethod
    def use(self, character: "Character") -> str: ...

    def __repr__(self) -> str:
        return f"[{self.item_type.value}] {self.name} ({self.weight}кг)"


class Weapon(Item):
    def __init__(self, name: str, weight: float, damage: int, range_: float):
        super().__init__(name, weight, 1, 4, ItemType.WEAPON)
        self.damage = damage
        self.range_ = range_
        self.slot   = EquipSlot.WEAPON

    def use(self, character: "Character") -> str:
        return (f"{character.name} атакує «{self.name}»! "
                f"Шкода: {self.damage}, Дальність: {self.range_}м")


class Armor(Item):
    def __init__(self, name: str, weight: float, defense: int, slot: EquipSlot):
        super().__init__(name, weight, 2, 3, ItemType.ARMOR)
        self.defense = defense
        self.slot    = slot

    def use(self, character: "Character") -> str:
        return f"Броня «{self.name}» надягнута. Захист +{self.defense}"


class Consumable(Item):
    def __init__(self, name: str, weight: float,
                 heal_amount: int, duration: int, effect: str):
        super().__init__(name, weight, 1, 1, ItemType.CONSUMABLE)
        self.heal_amount = heal_amount
        self.duration    = duration
        self.effect      = effect

    def use(self, character: "Character") -> str:
        character.heal(self.heal_amount)
        return f"«{self.name}»: +{self.heal_amount} HP. Ефект: {self.effect}"


class Resource(Item):
    def __init__(self, name: str, weight: float, quantity: int):
        super().__init__(name, weight, 1, 1, ItemType.RESOURCE)
        self.quantity = quantity

    def use(self, character: "Character") -> str:
        return f"Ресурс «{self.name}» (кількість: {self.quantity})"
