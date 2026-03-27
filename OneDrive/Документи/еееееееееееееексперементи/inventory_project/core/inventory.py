from __future__ import annotations
from typing import Optional
from models.items import Item
from core.observer import IInventoryObserver
from core.grid import InventoryGrid


class Inventory:
    """Клас інвентарю з Observer та Composite."""

    MAX_WEIGHT: float = 25.0

    def __init__(self, grid_rows: int = 8, grid_cols: int = 6):
        self._items:       list[Item]                   = []
        self._grid:        InventoryGrid                = InventoryGrid(grid_rows, grid_cols)
        self._observers:   list[IInventoryObserver]     = []
        self._quick_slots: list[Optional[Item]]         = [None] * 4

    # ── Observer ──────────────────────────────────────────────
    def subscribe(self, observer: IInventoryObserver) -> None:
        self._observers.append(observer)

    def unsubscribe(self, observer: IInventoryObserver) -> None:
        self._observers.remove(observer)

    def _notify(self, message: str) -> None:
        for obs in self._observers:
            obs.on_inventory_changed(message)

    # ── Властивості ───────────────────────────────────────────
    @property
    def current_weight(self) -> float:
        return sum(i.weight for i in self._items)

    @property
    def items(self) -> list[Item]:
        return list(self._items)

    # ── Операції ──────────────────────────────────────────────
    def add_item(self, item: Item) -> bool:
        if self.current_weight + item.weight > self.MAX_WEIGHT:
            self._notify(f"❌ Перевищення ваги: не можна додати «{item.name}»")
            return False
        if not self._grid.try_place(item):
            self._notify(f"❌ Немає місця в сітці для «{item.name}»")
            return False
        self._items.append(item)
        self._notify(f"✅ Додано: {item.name}")
        return True

    def remove_item(self, item: Item) -> bool:
        if item not in self._items:
            return False
        self._grid.remove(item)
        self._items.remove(item)
        self._notify(f"🗑 Видалено: {item.name}")
        return True

    # ── Швидкі слоти ──────────────────────────────────────────
    def assign_quick_slot(self, item: Item, slot: int) -> bool:
        if not (0 <= slot < 4) or item not in self._items:
            return False
        self._quick_slots[slot] = item
        self._notify(f"⚡ Швидкий слот [{slot + 1}]: {item.name}")
        return True

    def get_quick_slot(self, slot: int) -> Optional[Item]:
        return self._quick_slots[slot] if 0 <= slot < 4 else None

    def clear_quick_slot(self, slot: int) -> None:
        if 0 <= slot < 4:
            self._quick_slots[slot] = None

    def get_item_at_grid(self, row: int, col: int) -> Optional[Item]:
        return self._grid.get_item_at(row, col)
