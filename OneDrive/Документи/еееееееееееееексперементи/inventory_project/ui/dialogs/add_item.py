from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional

from models.items import Item, Weapon, Armor, Consumable, Resource
from models.enums import EquipSlot
from utils.theme import BG2, BG3, TEXT, TEXT_DIM, BORDER


class AddItemDialog(tk.Toplevel):
    """Діалог створення нового предмета."""

    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.title("Додати предмет")
        self.configure(bg=BG2)
        self.resizable(False, False)
        self.grab_set()
        self.result_item: Optional[Item] = None

        self.columnconfigure(1, weight=1)

        self._type_var   = tk.StringVar(value="Weapon")
        self._slot_var   = tk.StringVar(value="BODY")
        self._name_var   = tk.StringVar(value="Новий предмет")
        self._weight_var = tk.DoubleVar(value=1.0)
        self._stat_var   = tk.IntVar(value=10)

        def lbl(text: str, row: int) -> None:
            tk.Label(self, text=text, bg=BG2, fg=TEXT_DIM,
                     font=("Segoe UI", 10), anchor="w").grid(
                row=row, column=0, padx=(16, 8), pady=8, sticky="w")

        lbl("Тип:", 0)
        ttk.Combobox(self, textvariable=self._type_var,
                     values=["Weapon", "Armor", "Consumable", "Resource"],
                     state="readonly", width=22,
                     font=("Segoe UI", 10)).grid(
            row=0, column=1, padx=(0, 16), pady=8, sticky="ew")

        lbl("Назва:", 1)
        tk.Entry(self, textvariable=self._name_var, bg=BG3, fg=TEXT,
                 insertbackground=TEXT, font=("Segoe UI", 10), width=24).grid(
            row=1, column=1, padx=(0, 16), pady=8, sticky="ew")

        lbl("Вага (кг):", 2)
        tk.Spinbox(self, textvariable=self._weight_var,
                   from_=0.1, to=20, increment=0.1, format="%.1f",
                   bg=BG3, fg=TEXT, font=("Segoe UI", 10), width=10).grid(
            row=2, column=1, padx=(0, 16), pady=8, sticky="w")

        lbl("Стат:", 3)
        tk.Spinbox(self, textvariable=self._stat_var,
                   from_=1, to=200, bg=BG3, fg=TEXT,
                   font=("Segoe UI", 10), width=10).grid(
            row=3, column=1, padx=(0, 16), pady=8, sticky="w")
        tk.Label(self, text="(damage / defense / heal / кількість)",
                 bg=BG2, fg=TEXT_DIM, font=("Segoe UI", 8)).grid(
            row=4, column=0, columnspan=2, padx=16, sticky="w")

        lbl("Слот броні:", 5)
        ttk.Combobox(self, textvariable=self._slot_var,
                     values=["BODY", "HEAD", "LEGS"],
                     state="readonly", width=22,
                     font=("Segoe UI", 10)).grid(
            row=5, column=1, padx=(0, 16), pady=8, sticky="ew")

        tk.Frame(self, bg=BORDER, height=1).grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=16, pady=(4, 0))

        btn_frame = tk.Frame(self, bg=BG2)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=14)

        tk.Button(btn_frame, text="✔  Додати", bg="#2a6a3a", fg=TEXT,
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  padx=20, pady=8, cursor="hand2",
                  command=self._create).pack(side="left", padx=10)
        tk.Button(btn_frame, text="✖  Скасувати", bg="#6a2a2a", fg=TEXT,
                  relief="flat", font=("Segoe UI", 10),
                  padx=20, pady=8, cursor="hand2",
                  command=self.destroy).pack(side="left", padx=10)

        self.update_idletasks()
        pw = master.winfo_x() + master.winfo_width() // 2
        ph = master.winfo_y() + master.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{pw - w // 2}+{ph - h // 2}")

    def _create(self) -> None:
        name   = self._name_var.get().strip() or "Предмет"
        weight = float(self._weight_var.get())
        stat   = int(self._stat_var.get())
        t = self._type_var.get()

        if t == "Weapon":
            self.result_item = Weapon(name, weight, stat, 1.5)
        elif t == "Armor":
            self.result_item = Armor(name, weight, stat, EquipSlot[self._slot_var.get()])
        elif t == "Consumable":
            self.result_item = Consumable(name, weight, stat, 0, "ефект")
        else:
            self.result_item = Resource(name, weight, stat)
        self.destroy()
