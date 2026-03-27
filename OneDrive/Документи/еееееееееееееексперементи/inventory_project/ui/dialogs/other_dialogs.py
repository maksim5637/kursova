from __future__ import annotations
import tkinter as tk
from typing import Optional

from models.items import Item
from models.enums import EquipSlot
from utils.theme import BG2, BG3, TEXT, ACCENT


class UnequipDialog(tk.Toplevel):
    """Діалог зняття спорядження."""

    def __init__(self, master: tk.Tk, equipped: list[tuple[EquipSlot, Item]]):
        super().__init__(master)
        self.title("Зняти спорядження")
        self.geometry("280x220")
        self.configure(bg=BG2)
        self.grab_set()
        self.chosen_slot: Optional[EquipSlot] = None

        tk.Label(self, text="Оберіть слот для зняття:",
                 bg=BG2, fg=TEXT, font=("Segoe UI", 10)).pack(pady=10)

        for slot, item in equipped:
            tk.Button(self, text=f"{slot.value}: {item.name}",
                      bg=BG3, fg=TEXT, relief="flat",
                      padx=10, pady=6, cursor="hand2",
                      command=lambda s=slot: self._choose(s)).pack(
                fill="x", padx=20, pady=2)

        tk.Button(self, text="Скасувати", bg="#6a2a2a", fg=TEXT,
                  relief="flat", padx=10, pady=6,
                  command=self.destroy).pack(pady=8)

    def _choose(self, slot: EquipSlot) -> None:
        self.chosen_slot = slot
        self.destroy()


class AssignQuickSlotDialog(tk.Toplevel):
    """Діалог призначення предмета у швидкий слот."""

    def __init__(self, master: tk.Tk, items: list[Item], slot_idx: int):
        super().__init__(master)
        self.title(f"Призначити у слот [{slot_idx + 1}]")
        self.geometry("280x300")
        self.configure(bg=BG2)
        self.grab_set()
        self.chosen_item: Optional[Item] = None

        tk.Label(self, text="Оберіть предмет:",
                 bg=BG2, fg=TEXT, font=("Segoe UI", 10)).pack(pady=8)

        frame = tk.Frame(self, bg=BG2)
        frame.pack(fill="both", expand=True, padx=12)

        sb = tk.Scrollbar(frame)
        sb.pack(side="right", fill="y")

        lb = tk.Listbox(frame, bg=BG3, fg=TEXT, relief="flat",
                        font=("Segoe UI", 9), yscrollcommand=sb.set,
                        selectbackground=ACCENT)
        lb.pack(fill="both", expand=True)
        sb.config(command=lb.yview)

        for item in items:
            lb.insert("end", f"{item.name}  ({item.weight}кг)")
        self._items = items
        self._lb    = lb

        tk.Button(self, text="✔ Призначити", bg="#2a5a8a", fg=TEXT,
                  relief="flat", padx=10, pady=6,
                  command=self._choose).pack(pady=6)

    def _choose(self) -> None:
        sel = self._lb.curselection()
        if sel:
            self.chosen_item = self._items[sel[0]]
        self.destroy()
