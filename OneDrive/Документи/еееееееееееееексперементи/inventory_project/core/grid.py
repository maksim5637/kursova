from __future__ import annotations
from typing import Optional
from models.items import Item


class GridCell:
    """Одна клітинка сітки — Composite."""

    def __init__(self):
        self.is_occupied: bool           = False
        self.occupied_by: Optional[Item] = None


class InventoryGrid:
    """Двовимірна сітка інвентарю — Composite Pattern."""

    def __init__(self, rows: int, cols: int):
        self.rows  = rows
        self.cols  = cols
        self._cells: list[list[GridCell]] = [
            [GridCell() for _ in range(cols)] for _ in range(rows)
        ]

    def try_place(self, item: Item) -> bool:
        for r in range(self.rows - item.grid_height + 1):
            for c in range(self.cols - item.grid_width + 1):
                if self._can_fit(r, c, item):
                    self._place(r, c, item)
                    item.grid_x, item.grid_y = c, r
                    return True
        return False

    def _can_fit(self, row: int, col: int, item: Item) -> bool:
        for r in range(row, row + item.grid_height):
            for c in range(col, col + item.grid_width):
                if self._cells[r][c].is_occupied:
                    return False
        return True

    def _place(self, row: int, col: int, item: Item) -> None:
        for r in range(row, row + item.grid_height):
            for c in range(col, col + item.grid_width):
                self._cells[r][c].is_occupied = True
                self._cells[r][c].occupied_by = item

    def remove(self, item: Item) -> None:
        for r in range(self.rows):
            for c in range(self.cols):
                if self._cells[r][c].occupied_by is item:
                    self._cells[r][c].is_occupied = False
                    self._cells[r][c].occupied_by = None
        item.grid_x = item.grid_y = -1

    def get_item_at(self, row: int, col: int) -> Optional[Item]:
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self._cells[row][col].occupied_by
        return None
