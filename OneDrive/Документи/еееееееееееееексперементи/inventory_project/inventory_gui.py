"""
╔════════════════════════════════════════╗
║   СИСТЕМА ІНВЕНТАРЮ — Tkinter GUI      ║
╚════════════════════════════════════════╝
Запуск: python3 inventory_gui.py
Залежності: лише стандартна бібліотека Python (tkinter вбудований)
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
from datetime import datetime


# ============================================================
#  ENUM-и
# ============================================================
class ItemType(Enum):
    WEAPON     = "Зброя"
    ARMOR      = "Броня"
    CONSUMABLE = "Зілля"
    RESOURCE   = "Ресурс"


class EquipSlot(Enum):
    WEAPON = "Зброя"
    HEAD   = "Голова"
    BODY   = "Тіло"
    LEGS   = "Ноги"
    NONE   = "—"


# ============================================================
#  OBSERVER
# ============================================================
class IInventoryObserver(ABC):
    @abstractmethod
    def on_inventory_changed(self, message: str) -> None: ...


# ============================================================
#  ПРЕДМЕТИ
# ============================================================
class Item(ABC):
    def __init__(self, name, weight, grid_w, grid_h, item_type):
        self.name        = name
        self.weight      = weight
        self.grid_width  = grid_w
        self.grid_height = grid_h
        self.item_type   = item_type
        self.grid_x: int = -1
        self.grid_y: int = -1

    @abstractmethod
    def use(self, character: "Character") -> str: ...

    def __repr__(self):
        return f"[{self.item_type.value}] {self.name} ({self.weight}кг)"


class Weapon(Item):
    def __init__(self, name, weight, damage, range_):
        super().__init__(name, weight, 1, 4, ItemType.WEAPON)
        self.damage = damage
        self.range_ = range_
        self.slot   = EquipSlot.WEAPON

    def use(self, character):
        msg = f"{character.name} атакує «{self.name}»! Шкода: {self.damage}, Дальність: {self.range_}м"
        return msg


class Armor(Item):
    def __init__(self, name, weight, defense, slot):
        super().__init__(name, weight, 2, 3, ItemType.ARMOR)
        self.defense = defense
        self.slot    = slot

    def use(self, character):
        return f"Броня «{self.name}» надягнута. Захист +{self.defense}"


class Consumable(Item):
    def __init__(self, name, weight, heal_amount, duration, effect):
        super().__init__(name, weight, 1, 1, ItemType.CONSUMABLE)
        self.heal_amount = heal_amount
        self.duration    = duration
        self.effect      = effect

    def use(self, character):
        character.heal(self.heal_amount)
        return f"«{self.name}»: +{self.heal_amount} HP. Ефект: {self.effect}"


class Resource(Item):
    def __init__(self, name, weight, quantity):
        super().__init__(name, weight, 1, 1, ItemType.RESOURCE)
        self.quantity = quantity

    def use(self, character):
        return f"Ресурс «{self.name}» (кількість: {self.quantity})"


# ============================================================
#  COMPOSITE — сітка інвентарю
# ============================================================
class GridCell:
    def __init__(self):
        self.is_occupied = False
        self.occupied_by: Optional[Item] = None


class InventoryGrid:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self._cells = [[GridCell() for _ in range(cols)] for _ in range(rows)]

    def try_place(self, item):
        for r in range(self.rows - item.grid_height + 1):
            for c in range(self.cols - item.grid_width + 1):
                if self._can_fit(r, c, item):
                    self._place(r, c, item)
                    item.grid_x, item.grid_y = c, r
                    return True
        return False

    def _can_fit(self, row, col, item):
        for r in range(row, row + item.grid_height):
            for c in range(col, col + item.grid_width):
                if self._cells[r][c].is_occupied:
                    return False
        return True

    def _place(self, row, col, item):
        for r in range(row, row + item.grid_height):
            for c in range(col, col + item.grid_width):
                self._cells[r][c].is_occupied = True
                self._cells[r][c].occupied_by = item

    def remove(self, item):
        for r in range(self.rows):
            for c in range(self.cols):
                if self._cells[r][c].occupied_by is item:
                    self._cells[r][c].is_occupied = False
                    self._cells[r][c].occupied_by = None
        item.grid_x = item.grid_y = -1

    def get_item_at(self, row, col) -> Optional[Item]:
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self._cells[row][col].occupied_by
        return None


# ============================================================
#  ІНВЕНТАР
# ============================================================
class Inventory:
    MAX_WEIGHT = 25.0

    def __init__(self, grid_rows=8, grid_cols=6):
        self._items: list[Item]                   = []
        self._grid                                = InventoryGrid(grid_rows, grid_cols)
        self._observers: list[IInventoryObserver] = []
        self._quick_slots: list[Optional[Item]]   = [None] * 4

    def subscribe(self, obs): self._observers.append(obs)
    def _notify(self, msg):
        for o in self._observers: o.on_inventory_changed(msg)

    @property
    def current_weight(self): return sum(i.weight for i in self._items)

    @property
    def items(self): return list(self._items)

    def add_item(self, item) -> bool:
        if self.current_weight + item.weight > self.MAX_WEIGHT:
            self._notify(f"❌ Перевищення ваги: не можна додати «{item.name}»")
            return False
        if not self._grid.try_place(item):
            self._notify(f"❌ Немає місця в сітці для «{item.name}»")
            return False
        self._items.append(item)
        self._notify(f"✅ Додано: {item.name}")
        return True

    def remove_item(self, item) -> bool:
        if item not in self._items: return False
        self._grid.remove(item)
        self._items.remove(item)
        self._notify(f"🗑 Видалено: {item.name}")
        return True

    def assign_quick_slot(self, item, slot) -> bool:
        if not (0 <= slot < 4) or item not in self._items: return False
        self._quick_slots[slot] = item
        self._notify(f"⚡ Швидкий слот [{slot+1}]: {item.name}")
        return True

    def get_quick_slot(self, slot) -> Optional[Item]:
        return self._quick_slots[slot] if 0 <= slot < 4 else None

    def clear_quick_slot(self, slot):
        if 0 <= slot < 4: self._quick_slots[slot] = None

    def get_item_at_grid(self, row, col) -> Optional[Item]:
        return self._grid.get_item_at(row, col)


# ============================================================
#  СПОРЯДЖЕННЯ — Strategy Pattern
# ============================================================
class Equipment:
    def __init__(self):
        self._slots: dict[EquipSlot, Optional[Item]] = {
            EquipSlot.WEAPON: None, EquipSlot.HEAD: None,
            EquipSlot.BODY:   None, EquipSlot.LEGS: None,
        }

    def _compatible(self, item, slot) -> bool:
        if isinstance(item, Weapon): return slot == EquipSlot.WEAPON
        if isinstance(item, Armor):  return item.slot == slot
        return False

    def equip(self, item, slot) -> tuple[bool, Optional[Item]]:
        if not self._compatible(item, slot): return False, None
        old = self._slots[slot]
        self._slots[slot] = item
        return True, old

    def unequip(self, slot) -> Optional[Item]:
        item = self._slots.get(slot)
        self._slots[slot] = None
        return item

    def get_item(self, slot) -> Optional[Item]:
        return self._slots.get(slot)

    def get_defense_bonus(self) -> int:
        return sum(i.defense for i in self._slots.values() if isinstance(i, Armor))

    def get_attack_bonus(self) -> int:
        return sum(i.damage for i in self._slots.values() if isinstance(i, Weapon))


# ============================================================
#  ПЕРСОНАЖ
# ============================================================
class Character:
    def __init__(self, name, max_hp=120):
        self.name      = name
        self.max_hp    = max_hp
        self.hp        = max_hp
        self.inventory = Inventory()
        self.equipment = Equipment()

    def heal(self, amount):
        self.hp = min(self.hp + amount, self.max_hp)

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def pick_up(self, item) -> bool:
        return self.inventory.add_item(item)

    def equip_item(self, item, slot) -> tuple[bool, str]:
        if item not in self.inventory.items:
            return False, f"«{item.name}» не в інвентарі"
        ok, old = self.equipment.equip(item, slot)
        if not ok:
            return False, f"«{item.name}» не підходить до слоту {slot.value}"
        if old:
            self.inventory.add_item(old)
        return True, f"Екіпіровано «{item.name}» → {slot.value}"

    def unequip_item(self, slot) -> tuple[bool, str]:
        item = self.equipment.unequip(slot)
        if not item: return False, "Слот порожній"
        self.inventory.add_item(item)
        return True, f"Знято «{item.name}»"

    def use_item(self, item) -> str:
        if item not in self.inventory.items:
            return f"«{item.name}» не знайдено"
        msg = item.use(self)
        if isinstance(item, Consumable):
            self.inventory.remove_item(item)
        return msg


# ============================================================
#  КОЛЬОРИ / СТИЛІ
# ============================================================
BG        = "#12121a"
BG2       = "#1a1a26"
BG3       = "#22223a"
ACCENT    = "#4a90d9"
ACCENT2   = "#f0c040"
GREEN     = "#4caf80"
RED       = "#e05050"
ORANGE    = "#e08030"
TEXT      = "#e8e8f0"
TEXT_DIM  = "#808090"
BORDER    = "#303050"

ITEM_COLORS = {
    ItemType.WEAPON:     ("#7a3a10", "#e0943a"),
    ItemType.ARMOR:      ("#1a3a6a", "#4a90d9"),
    ItemType.CONSUMABLE: ("#1a5a30", "#50c878"),
    ItemType.RESOURCE:   ("#3a2a5a", "#9070d0"),
}

CELL_SIZE = 52


# ============================================================
#  ГОЛОВНЕ ВІКНО
# ============================================================
class InventoryApp(tk.Tk, IInventoryObserver):
    def __init__(self):
        super().__init__()
        self.title("⚔  Система Інвентарю")
        self.geometry("1180x720")
        self.minsize(1000, 650)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.hero = Character("Артем", 120)
        self.hero.inventory.subscribe(self)

        self._selected_item:  Optional[Item]       = None
        self._drag_item:      Optional[Item]       = None
        self._drag_offset_x:  int                  = 0
        self._drag_offset_y:  int                  = 0
        self._drag_ghost_id:  Optional[int]        = None  # canvas ghost item
        self._drop_highlight: Optional[tuple]      = None  # (r,c) підсвічена клітинка

        self._build_ui()
        self._seed_items()
        self._refresh_all()

    # ── Observer ──
    def on_inventory_changed(self, message: str):
        self._log(message)
        self._refresh_all()

    # ──────────────────────────────────────────────────────────
    #  ПОБУДОВА UI
    # ──────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Верхня смуга ──
        top = tk.Frame(self, bg=BG2, height=52)
        top.pack(fill="x", side="top")
        top.pack_propagate(False)

        tk.Label(top, text="⚔  СИСТЕМА ІНВЕНТАРЮ", bg=BG2,
                 fg=ACCENT2, font=("Segoe UI", 14, "bold")).pack(side="left", padx=16)

        self._lbl_hp     = tk.Label(top, text="", bg=BG2, fg=GREEN,  font=("Segoe UI", 10))
        self._lbl_stats  = tk.Label(top, text="", bg=BG2, fg=ACCENT, font=("Segoe UI", 10))
        self._lbl_weight = tk.Label(top, text="", bg=BG2, fg=ORANGE, font=("Segoe UI", 10))
        self._lbl_hp.pack(side="left", padx=24)
        self._lbl_stats.pack(side="left", padx=24)
        self._lbl_weight.pack(side="left", padx=24)

        # ── Нижня кнопочна смуга ──
        bot = tk.Frame(self, bg=BG2, height=46)
        bot.pack(fill="x", side="bottom")
        bot.pack_propagate(False)

        btns = [
            ("➕ Додати предмет",    "#2a6a3a", self._dialog_add_item),
            ("▶ Використати",        "#2a3a7a", self._use_selected),
            ("⚔ Екіпірувати",        "#5a3a10", self._equip_selected),
            ("↩ Зняти спорядження",  "#3a2a5a", self._dialog_unequip),
            ("🗑 Викинути",           "#6a1a1a", self._drop_selected),
            ("💔 Отримати удар −20", "#7a3a10", self._take_hit),
        ]
        for txt, color, cmd in btns:
            b = tk.Button(bot, text=txt, bg=color, fg=TEXT, relief="flat",
                          font=("Segoe UI", 9), padx=10, pady=6, cursor="hand2",
                          activebackground=ACCENT, activeforeground="white", command=cmd)
            b.pack(side="left", padx=4, pady=6)

        # ── Основний layout ──
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=6, pady=4)

        # Лівий стовпець (швидкі слоти + лог)
        left = tk.Frame(main, bg=BG, width=190)
        left.pack(side="left", fill="y", padx=(0, 4))
        left.pack_propagate(False)
        self._build_quick_slots(left)
        self._build_log(left)

        # Центр (сітка)
        center = tk.Frame(main, bg=BG)
        center.pack(side="left", fill="both", expand=True, padx=4)
        self._build_grid(center)

        # Правий стовпець (спорядження + секції)
        right = tk.Frame(main, bg=BG, width=270)
        right.pack(side="left", fill="y", padx=(4, 0))
        right.pack_propagate(False)
        self._build_equipment_panel(right)
        self._build_sections_panel(right)

    # ── Швидкі слоти ──
    def _build_quick_slots(self, parent):
        frame = self._panel(parent, "⚡ ШВИДКІ СЛОТИ")
        frame.pack(fill="x", pady=(0, 4))

        self._qs_btns: list[tk.Button] = []
        for i in range(4):
            btn = tk.Button(
                frame, text=f"[{i+1}]  —", bg=BG3, fg=TEXT_DIM,
                relief="flat", font=("Segoe UI", 9), anchor="w", padx=8,
                cursor="hand2", activebackground=ACCENT,
                command=lambda idx=i: self._use_quick_slot(idx)
            )
            btn.pack(fill="x", padx=6, pady=2, ipady=6)

            # ПКМ — контекстне меню
            btn.bind("<Button-3>", lambda e, idx=i: self._qs_context(e, idx))
            self._qs_btns.append(btn)

    # ── Лог ──
    def _build_log(self, parent):
        frame = self._panel(parent, "📋 ЛОГ ПОДІЙ")
        frame.pack(fill="both", expand=True)

        self._log_text = tk.Text(
            frame, bg="#0e0e18", fg=TEXT_DIM, relief="flat",
            font=("Consolas", 8), wrap="word", state="disabled",
            cursor="arrow"
        )
        sb = tk.Scrollbar(frame, command=self._log_text.yview, bg=BG3)
        self._log_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._log_text.pack(fill="both", expand=True, padx=4, pady=4)

    # ── Сітка інвентарю ──
    def _build_grid(self, parent):
        hdr = self._panel_header(parent, "🎒 ІНВЕНТАР  (клік — вибір, ПКМ — меню)")
        hdr.pack(fill="x")

        hint = tk.Label(parent,
                        text="Подвійний клік → екіпірувати/використати  |  Затисни та тягни → перемістити",
                        bg=BG, fg=TEXT_DIM, font=("Segoe UI", 8))
        hint.pack()

        canvas_frame = tk.Frame(parent, bg=BG)
        canvas_frame.pack(fill="both", expand=True, padx=4, pady=4)

        rows, cols = 8, 6
        w = cols * CELL_SIZE + 2
        h = rows * CELL_SIZE + 2

        self._canvas = tk.Canvas(canvas_frame, width=w, height=h,
                                  bg="#0e0e18", highlightthickness=1,
                                  highlightbackground=BORDER)
        self._canvas.pack(anchor="nw")
        self._canvas.bind("<Button-1>",        self._grid_click)
        self._canvas.bind("<Double-Button-1>",  self._grid_dbl_click)
        self._canvas.bind("<Button-3>",         self._grid_rclick)
        self._canvas.bind("<Motion>",           self._grid_hover)
        self._canvas.bind("<B1-Motion>",        self._drag_motion)
        self._canvas.bind("<ButtonRelease-1>",  self._drag_release)

        self._grid_rows = rows
        self._grid_cols = cols
        self._hover_cell: tuple[int,int] = (-1, -1)

    # ── Спорядження ──
    def _build_equipment_panel(self, parent):
        frame = self._panel(parent, "🛡 СПОРЯДЖЕННЯ")
        frame.pack(fill="x", pady=(0, 4))

        self._equip_labels: dict[EquipSlot, tk.Label] = {}
        slot_info = [
            (EquipSlot.WEAPON, "⚔ Зброя"),
            (EquipSlot.HEAD,   "🪖 Голова"),
            (EquipSlot.BODY,   "🥋 Тіло"),
            (EquipSlot.LEGS,   "👢 Ноги"),
        ]
        for slot, label in slot_info:
            row = tk.Frame(frame, bg=BG3)
            row.pack(fill="x", padx=6, pady=2)
            tk.Label(row, text=label, bg=BG3, fg=TEXT_DIM,
                     font=("Segoe UI", 9), width=9, anchor="w").pack(side="left", padx=4)
            lbl = tk.Label(row, text="—", bg="#1a1a2e", fg=TEXT_DIM,
                           font=("Segoe UI", 9), anchor="w", padx=6,
                           relief="flat", bd=1, cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True, padx=(0,4), pady=2, ipady=4)
            lbl.bind("<Double-Button-1>", lambda e, s=slot: self._unequip_slot(s))
            self._equip_labels[slot] = lbl

        self._lbl_bonuses = tk.Label(frame, text="", bg=BG3, fg=ACCENT2,
                                      font=("Segoe UI", 9))
        self._lbl_bonuses.pack(pady=(4, 6))

    # ── Секції предметів ──
    def _build_sections_panel(self, parent):
        outer = self._panel(parent, "📦 ПРЕДМЕТИ ЗА ТИПОМ")
        outer.pack(fill="both", expand=True)

        scroll_canvas = tk.Canvas(outer, bg=BG2, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        scroll_canvas.pack(side="left", fill="both", expand=True)

        self._sections_inner = tk.Frame(scroll_canvas, bg=BG2)
        win = scroll_canvas.create_window((0,0), window=self._sections_inner, anchor="nw")

        def on_configure(e):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
            scroll_canvas.itemconfig(win, width=scroll_canvas.winfo_width())
        self._sections_inner.bind("<Configure>", on_configure)
        scroll_canvas.bind("<Configure>", lambda e: scroll_canvas.itemconfig(win, width=e.width))

        self._section_frames: dict[ItemType, tk.Frame] = {}
        self._section_hdrs:   dict[ItemType, tk.Button] = {}
        self._section_open:   dict[ItemType, bool]     = {t: True for t in ItemType}
        icons = {ItemType.WEAPON:"⚔", ItemType.ARMOR:"🛡",
                 ItemType.CONSUMABLE:"🧪", ItemType.RESOURCE:"📦"}

        for itype in ItemType:
            # Контейнер для всієї секції (заголовок + вміст)
            section_box = tk.Frame(self._sections_inner, bg=BG2)
            section_box.pack(fill="x", pady=(4, 0))

            hdr = tk.Button(
                section_box, text=f"{icons[itype]} {itype.value}  ▼",
                bg="#2a3a5a", fg="#a0c0ff", relief="flat",
                font=("Segoe UI", 9, "bold"), anchor="w", padx=8,
                cursor="hand2", command=lambda t=itype: self._toggle_section(t)
            )
            hdr.pack(fill="x")

            content = tk.Frame(section_box, bg=BG2)
            content.pack(fill="x")

            self._section_frames[itype] = content
            self._section_hdrs[itype]   = hdr


    # ──────────────────────────────────────────────────────────
    #  DRAG & DROP
    # ──────────────────────────────────────────────────────────
    def _drag_motion(self, event):
        """Рух миші з затиснутою кнопкою — малюємо ghost предмет."""
        if not self._drag_item:
            return

        item = self._drag_item

        # Оновлюємо підсвітку цільової клітинки
        target_col = (event.x - self._drag_offset_x) // CELL_SIZE
        target_row = (event.y - self._drag_offset_y) // CELL_SIZE
        # Притискаємо до меж сітки
        target_col = max(0, min(target_col, self._grid_cols - item.grid_width))
        target_row = max(0, min(target_row, self._grid_rows - item.grid_height))
        self._drop_highlight = (target_row, target_col)

        # Перемальовуємо сітку (підсвітка + всі предмети крім drag)
        self._draw_grid_drag(item, event.x, event.y)

    def _drag_release(self, event):
        """Відпустили кнопку миші — виконуємо переміщення."""
        if not self._drag_item:
            return

        item = self._drag_item
        target_col = (event.x - self._drag_offset_x) // CELL_SIZE
        target_row = (event.y - self._drag_offset_y) // CELL_SIZE
        target_col = max(0, min(target_col, self._grid_cols - item.grid_width))
        target_row = max(0, min(target_row, self._grid_rows - item.grid_height))

        # Якщо позиція не змінилась — нічого не робимо
        if target_col != item.grid_x or target_row != item.grid_y:
            if self._can_drop_at(target_row, target_col, item):
                self._move_item_in_grid(item, target_row, target_col)
                self._log(f"↕ Переміщено «{item.name}» → ({target_col},{target_row})")
            else:
                self._log(f"❌ Неможливо перемістити «{item.name}» — місце зайняте")

        # Скидаємо drag-стан
        self._drag_item       = None
        self._drop_highlight  = None
        self._hover_cell      = (-1, -1)
        self._draw_grid()

    def _can_drop_at(self, row: int, col: int, item: "Item") -> bool:
        """Перевіряємо чи можна розмістити предмет на нову позицію."""
        # Вихід за межі сітки
        if (row < 0 or col < 0 or
                row + item.grid_height > self._grid_rows or
                col + item.grid_width  > self._grid_cols):
            return False
        # Перевіряємо клітинки (ігноруємо самого себе)
        for r in range(row, row + item.grid_height):
            for c in range(col, col + item.grid_width):
                cell_item = self.hero.inventory.get_item_at_grid(r, c)
                if cell_item is not None and cell_item is not item:
                    return False
        return True

    def _move_item_in_grid(self, item: "Item", new_row: int, new_col: int) -> None:
        """Переміщуємо предмет на нову позицію в сітці."""
        # Звільняємо старі клітинки
        self.hero.inventory._grid.remove(item)
        # Встановлюємо нові координати вручну
        item.grid_x = new_col
        item.grid_y = new_row
        # Заповнюємо нові клітинки
        for r in range(new_row, new_row + item.grid_height):
            for c in range(new_col, new_col + item.grid_width):
                self.hero.inventory._grid._cells[r][c].is_occupied = True
                self.hero.inventory._grid._cells[r][c].occupied_by = item

    def _draw_grid_drag(self, drag_item: "Item", mouse_x: int, mouse_y: int) -> None:
        """Малюємо сітку під час drag — з ghost-предметом під курсором."""
        c = self._canvas
        c.delete("all")
        rows, cols = self._grid_rows, self._grid_cols

        # Фон клітинок з підсвіткою
        for r in range(rows):
            for col in range(cols):
                x1 = col * CELL_SIZE + 1
                y1 = r   * CELL_SIZE + 1
                x2 = x1 + CELL_SIZE - 1
                y2 = y1 + CELL_SIZE - 1

                fill = "#181828"
                if self._drop_highlight:
                    dr, dc = self._drop_highlight
                    in_zone = (dr <= r < dr + drag_item.grid_height and
                               dc <= col < dc + drag_item.grid_width)
                    if in_zone:
                        can = self._can_drop_at(dr, dc, drag_item)
                        fill = "#1a4a1a" if can else "#4a1a1a"
                c.create_rectangle(x1, y1, x2, y2, fill=fill, outline=BORDER, width=1)

        # Малюємо всі предмети крім того що тягнемо
        drawn: set[int] = set()
        for item in self.hero.inventory.items:
            if item is drag_item: continue
            if id(item) in drawn or item.grid_x < 0: continue
            drawn.add(id(item))
            self._draw_item_on_canvas(c, item, alpha=True)

        # Ghost предмет під курсором (напівпрозорий)
        gx = mouse_x - self._drag_offset_x
        gy = mouse_y - self._drag_offset_y
        x1, y1 = gx + 3, gy + 3
        x2 = x1 + drag_item.grid_width  * CELL_SIZE - 6
        y2 = y1 + drag_item.grid_height * CELL_SIZE - 6
        fill, border_color = ITEM_COLORS.get(drag_item.item_type, ("#333", "#888"))
        # Тінь ghost
        c.create_rectangle(x1+4, y1+4, x2+4, y2+4, fill="#000000", outline="", stipple="gray50")
        # Ghost тіло (світліше)
        c.create_rectangle(x1, y1, x2, y2,
                           fill=fill, outline=ACCENT2, width=2,
                           stipple="gray75")
        short = drag_item.name if len(drag_item.name) <= 11 else drag_item.name[:10] + "…"
        c.create_text(x1+5, y1+5, text=short,
                      fill=TEXT, font=("Segoe UI", 8, "bold"), anchor="nw")

    def _draw_item_on_canvas(self, c, item: "Item", alpha: bool = False) -> None:
        """Малює один предмет на canvas."""
        if item.grid_x < 0: return
        x1 = item.grid_x * CELL_SIZE + 3
        y1 = item.grid_y * CELL_SIZE + 3
        x2 = x1 + item.grid_width  * CELL_SIZE - 5
        y2 = y1 + item.grid_height * CELL_SIZE - 5
        fill, border_color = ITEM_COLORS.get(item.item_type, ("#333", "#888"))
        selected = item is self._selected_item
        c.create_rectangle(x1+3, y1+3, x2+3, y2+3, fill="#000000", outline="")
        c.create_rectangle(x1, y1, x2, y2, fill=fill,
                           outline=ACCENT2 if selected else border_color,
                           width=2 if selected else 1)
        short = item.name if len(item.name) <= 11 else item.name[:10] + "…"
        c.create_text(x1+5, y1+5, text=short,
                      fill=TEXT, font=("Segoe UI", 8, "bold"), anchor="nw")
        c.create_text(x1+5, y2-5, text=f"{item.weight}кг",
                      fill=TEXT_DIM, font=("Segoe UI", 7), anchor="sw")
        icons = {ItemType.WEAPON:"⚔", ItemType.ARMOR:"🛡",
                 ItemType.CONSUMABLE:"🧪", ItemType.RESOURCE:"📦"}
        c.create_text(x2-4, y1+4, text=icons.get(item.item_type, "?"),
                      fill=border_color, font=("Segoe UI", 9), anchor="ne")

    # ──────────────────────────────────────────────────────────
    #  МАЛЮВАННЯ СІТКИ
    # ──────────────────────────────────────────────────────────
    def _draw_grid(self):
        c = self._canvas
        c.delete("all")
        rows, cols = self._grid_rows, self._grid_cols

        # Клітинки фону
        for r in range(rows):
            for col in range(cols):
                x1 = col * CELL_SIZE + 1
                y1 = r * CELL_SIZE + 1
                x2 = x1 + CELL_SIZE - 1
                y2 = y1 + CELL_SIZE - 1
                hover = (r, col) == self._hover_cell

                # Підсвітка зони куди скидаємо предмет
                if self._drop_highlight and self._drag_item:
                    dr, dc = self._drop_highlight
                    item = self._drag_item
                    in_drop = (dr <= r < dr + item.grid_height and
                               dc <= col < dc + item.grid_width)
                    # Перевіряємо чи вміщується
                    can = self._can_drop_at(dr, dc, item)
                    if in_drop:
                        fill = "#1a4a1a" if can else "#4a1a1a"
                        c.create_rectangle(x1, y1, x2, y2,
                                           fill=fill, outline=BORDER, width=1)
                        continue

                c.create_rectangle(x1, y1, x2, y2,
                                   fill="#181828" if not hover else "#222240",
                                   outline=BORDER, width=1)

        # Предмети — використовуємо спільний метод
        drawn: set[int] = set()
        for item in self.hero.inventory.items:
            if id(item) in drawn or item.grid_x < 0: continue
            drawn.add(id(item))
            self._draw_item_on_canvas(c, item)

    # ──────────────────────────────────────────────────────────
    #  ОНОВЛЕННЯ ВСЬОГО UI
    # ──────────────────────────────────────────────────────────
    def _refresh_all(self):
        self._refresh_top()
        self._refresh_equipment()
        self._refresh_sections()
        self._refresh_quick_slots()
        self._draw_grid()

    def _refresh_top(self):
        h = self.hero
        self._lbl_hp.config(
            text=f"❤  HP: {h.hp} / {h.max_hp}",
            fg=RED if h.hp < 40 else GREEN
        )
        self._lbl_stats.config(
            text=f"⚔ Атака: {h.equipment.get_attack_bonus()}  │  🛡 Захист: {h.equipment.get_defense_bonus()}"
        )
        w = h.inventory.current_weight
        self._lbl_weight.config(
            text=f"⚖  {w:.1f} / {Inventory.MAX_WEIGHT} кг",
            fg=RED if w > 22 else ORANGE
        )

    def _refresh_equipment(self):
        for slot, lbl in self._equip_labels.items():
            item = self.hero.equipment.get_item(slot)
            if item:
                _, bc = ITEM_COLORS.get(item.item_type, ("#333", "#aaa"))
                lbl.config(text=f"  {item.name}", fg=bc)
            else:
                lbl.config(text="  —", fg=TEXT_DIM)
        self._lbl_bonuses.config(
            text=f"Атака: +{self.hero.equipment.get_attack_bonus()}"
                 f"  │  Захист: +{self.hero.equipment.get_defense_bonus()}"
        )

    def _refresh_sections(self):
        for itype, frame in self._section_frames.items():
            # Очищаємо вміст
            for w in frame.winfo_children(): w.destroy()

            if not self._section_open[itype]:
                # Повністю ховаємо content-фрейм — місце зникає
                frame.pack_forget()
                continue

            # Повертаємо фрейм на місце (після заголовка вже запаковано в section_box)
            frame.pack(fill="x")

            items = [i for i in self.hero.inventory.items if i.item_type == itype]
            if not items:
                tk.Label(frame, text="  (порожньо)", bg=BG2, fg=TEXT_DIM,
                         font=("Segoe UI", 8)).pack(anchor="w", padx=8, pady=2)
            for item in items:
                sel = item is self._selected_item
                _, bc = ITEM_COLORS.get(item.item_type, ("#333", "#aaa"))
                btn = tk.Button(
                    frame, text=f"  {item.name}  ({item.weight}кг)",
                    bg="#1e2035" if not sel else "#2a3a5a",
                    fg=bc if sel else TEXT,
                    relief="flat", font=("Segoe UI", 9), anchor="w",
                    cursor="hand2",
                    command=lambda i=item: self._select_item(i)
                )
                btn.pack(fill="x", padx=4, pady=1, ipady=3)
                btn.bind("<Button-3>", lambda e, i=item: self._item_context(e, i))
                btn.bind("<Double-Button-1>", lambda e, i=item: self._quick_action(i))

    def _refresh_quick_slots(self):
        for i, btn in enumerate(self._qs_btns):
            item = self.hero.inventory.get_quick_slot(i)
            if item:
                _, bc = ITEM_COLORS.get(item.item_type, ("#333", "#aaa"))
                btn.config(text=f"[{i+1}]  {item.name}", fg=bc)
            else:
                btn.config(text=f"[{i+1}]  —", fg=TEXT_DIM)

    # ──────────────────────────────────────────────────────────
    #  ПОДІЇ СІТКИ
    # ──────────────────────────────────────────────────────────
    def _grid_coords(self, event):
        return event.y // CELL_SIZE, event.x // CELL_SIZE

    def _grid_click(self, event):
        r, c = self._grid_coords(event)
        item = self.hero.inventory.get_item_at_grid(r, c)
        self._select_item(item)
        # Запам'ятовуємо зміщення всередині предмета для drag
        if item:
            self._drag_item    = item
            self._drag_offset_x = event.x - item.grid_x * CELL_SIZE
            self._drag_offset_y = event.y - item.grid_y * CELL_SIZE
        else:
            self._drag_item = None

    def _grid_dbl_click(self, event):
        r, c = self._grid_coords(event)
        item = self.hero.inventory.get_item_at_grid(r, c)
        if item: self._quick_action(item)

    def _grid_rclick(self, event):
        r, c = self._grid_coords(event)
        item = self.hero.inventory.get_item_at_grid(r, c)
        if item: self._item_context(event, item)

    def _grid_hover(self, event):
        if self._drag_item:
            return  # під час drag hover не потрібен
        cell = (event.y // CELL_SIZE, event.x // CELL_SIZE)
        if cell != self._hover_cell:
            self._hover_cell = cell
            self._draw_grid()

    # ──────────────────────────────────────────────────────────
    #  ДІЇ З ПРЕДМЕТАМИ
    # ──────────────────────────────────────────────────────────
    def _select_item(self, item: Optional[Item]):
        self._selected_item = item
        self._draw_grid()
        self._refresh_sections()
        if item:
            self._log(f"🔍 Обрано: {item}")

    def _quick_action(self, item: Item):
        """Подвійний клік: для зілля — використати, для решти — екіпірувати."""
        if isinstance(item, Consumable):
            msg = self.hero.use_item(item)
            self._log(f"💊 {msg}")
        elif isinstance(item, (Weapon, Armor)):
            self._equip_item(item)
        else:
            msg = self.hero.use_item(item)
            self._log(f"▶ {msg}")
        self._refresh_all()

    def _use_selected(self):
        if not self._selected_item:
            messagebox.showinfo("Увага", "Спочатку оберіть предмет (клік по сітці або списку)")
            return
        msg = self.hero.use_item(self._selected_item)
        self._log(f"▶ {msg}")
        self._selected_item = None
        self._refresh_all()

    def _equip_selected(self):
        item = self._selected_item
        if not item:
            messagebox.showinfo("Увага", "Спочатку оберіть предмет")
            return
        if isinstance(item, Weapon):
            ok, msg = self.hero.equip_item(item, EquipSlot.WEAPON)
        elif isinstance(item, Armor):
            ok, msg = self.hero.equip_item(item, item.slot)
        else:
            ok, msg = False, f"«{item.name}» не можна екіпірувати"
        self._log(("✅ " if ok else "❌ ") + msg)
        self._refresh_all()

    def _equip_item(self, item: Item):
        if isinstance(item, Weapon):
            ok, msg = self.hero.equip_item(item, EquipSlot.WEAPON)
        elif isinstance(item, Armor):
            ok, msg = self.hero.equip_item(item, item.slot)
        else:
            ok, msg = False, "Не можна екіпірувати"
        self._log(("✅ " if ok else "❌ ") + msg)
        self._refresh_all()

    def _drop_selected(self):
        item = self._selected_item
        if not item:
            messagebox.showinfo("Увага", "Спочатку оберіть предмет")
            return
        if messagebox.askyesno("Підтвердження", f"Викинути «{item.name}»?"):
            self.hero.inventory.remove_item(item)
            self._selected_item = None
            self._refresh_all()

    def _unequip_slot(self, slot: EquipSlot):
        ok, msg = self.hero.unequip_item(slot)
        self._log(("✅ " if ok else "❌ ") + msg)
        self._refresh_all()

    def _dialog_unequip(self):
        slots = [(s, self.hero.equipment.get_item(s)) for s in EquipSlot if s != EquipSlot.NONE]
        equipped = [(s, i) for s, i in slots if i]
        if not equipped:
            messagebox.showinfo("Увага", "Немає екіпірованих предметів")
            return
        dlg = UnequipDialog(self, equipped)
        self.wait_window(dlg)
        if dlg.chosen_slot:
            self._unequip_slot(dlg.chosen_slot)

    def _take_hit(self):
        self.hero.take_damage(20)
        self._log(f"💔 Отримано 20 пошкодження. HP = {self.hp}/{self.hero.max_hp}")
        self._refresh_all()

    def _use_quick_slot(self, idx: int):
        item = self.hero.inventory.get_quick_slot(idx)
        if not item:
            self._log(f"⚡ Швидкий слот [{idx+1}] порожній")
            return
        self._quick_action(item)

    def _qs_context(self, event, idx: int):
        item = self.hero.inventory.get_quick_slot(idx)
        menu = tk.Menu(self, tearoff=0, bg=BG3, fg=TEXT)
        if item:
            menu.add_command(label=f"▶ Використати «{item.name}»",
                             command=lambda: self._use_quick_slot(idx))
            menu.add_separator()
            menu.add_command(label="✖ Очистити слот",
                             command=lambda: (self.hero.inventory.clear_quick_slot(idx),
                                             self._refresh_quick_slots()))
        else:
            # Призначити предмет
            items = self.hero.inventory.items
            if items:
                menu.add_command(label="Призначити предмет...",
                                 command=lambda: self._dialog_assign_qs(idx))
            else:
                menu.add_command(label="Інвентар порожній", state="disabled")
        menu.post(event.x_root, event.y_root)

    def _dialog_assign_qs(self, idx: int):
        dlg = AssignQuickSlotDialog(self, self.hero.inventory.items, idx)
        self.wait_window(dlg)
        if dlg.chosen_item:
            self.hero.inventory.assign_quick_slot(dlg.chosen_item, idx)
            self._refresh_quick_slots()

    def _item_context(self, event, item: Item):
        menu = tk.Menu(self, tearoff=0, bg=BG3, fg=TEXT,
                       activebackground=ACCENT, activeforeground="white")
        menu.add_command(label=f"🔍 {item.name}  ({item.weight}кг)", state="disabled",
                         font=("Segoe UI", 9, "bold"))
        menu.add_separator()
        menu.add_command(label="▶ Використати",
                         command=lambda: (setattr(self, '_selected_item', item),
                                         self._use_selected()))
        if isinstance(item, (Weapon, Armor)):
            menu.add_command(label="⚔ Екіпірувати",
                             command=lambda: self._equip_item(item))
        menu.add_separator()
        for i in range(4):
            menu.add_command(label=f"⚡ Призначити у слот [{i+1}]",
                             command=lambda i=i: self.hero.inventory.assign_quick_slot(item, i)
                             or self._refresh_quick_slots())
        menu.add_separator()
        menu.add_command(label="🗑 Викинути",
                         command=lambda: (
                             messagebox.askyesno("Підтвердження", f"Викинути «{item.name}»?") and (
                                 self.hero.inventory.remove_item(item),
                                 setattr(self, '_selected_item', None),
                                 self._refresh_all()
                             )
                         ))
        menu.post(event.x_root, event.y_root)

    def _toggle_section(self, itype: ItemType):
        self._section_open[itype] = not self._section_open[itype]
        icon = "▼" if self._section_open[itype] else "▶"
        icons = {ItemType.WEAPON:"⚔", ItemType.ARMOR:"🛡",
                 ItemType.CONSUMABLE:"🧪", ItemType.RESOURCE:"📦"}
        self._section_hdrs[itype].config(text=f"{icons[itype]} {itype.value}  {icon}")
        self._refresh_sections()

    # ── Діалог додавання предмета ──
    def _dialog_add_item(self):
        dlg = AddItemDialog(self)
        self.wait_window(dlg)
        if dlg.result_item:
            ok = self.hero.pick_up(dlg.result_item)
            if ok:
                # Авто-призначення у перший вільний швидкий слот
                for i in range(4):
                    if self.hero.inventory.get_quick_slot(i) is None:
                        self.hero.inventory.assign_quick_slot(dlg.result_item, i)
                        break
            self._refresh_all()

    # ──────────────────────────────────────────────────────────
    #  ДОПОМІЖНІ
    # ──────────────────────────────────────────────────────────
    def _log(self, msg: str):
        ts  = datetime.now().strftime("%H:%M:%S")
        self._log_text.configure(state="normal")
        self._log_text.insert("end", f"{ts}  {msg}\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    @staticmethod
    def _panel(parent, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg=BG2, bd=1, relief="flat",
                         highlightbackground=BORDER, highlightthickness=1)
        tk.Label(outer, text=title, bg="#1e1e30", fg=ACCENT,
                 font=("Segoe UI", 9, "bold"), anchor="w", padx=8,
                 pady=4).pack(fill="x")
        return outer

    @staticmethod
    def _panel_header(parent, title: str) -> tk.Frame:
        f = tk.Frame(parent, bg=BG2)
        tk.Label(f, text=title, bg=BG2, fg=ACCENT,
                 font=("Segoe UI", 9, "bold"), anchor="w", padx=8,
                 pady=4).pack(fill="x")
        return f

    # ── Початкові предмети ──
    def _seed_items(self):
        items = [
            Weapon("Сталевий меч",    3.5, 25, 1.5),
            Weapon("Ельфійський лук", 2.0, 18, 30.0),
            Armor("Нагрудник лицаря", 8.0, 30, EquipSlot.BODY),
            Armor("Шолом варвара",    3.0, 15, EquipSlot.HEAD),
            Consumable("Мале зілля",  0.3, 30, 0,  "миттєве зцілення"),
            Consumable("Велике зілля",0.5, 80, 5,  "регенерація"),
            Resource("Дерево",        0.5, 10),
            Resource("Залізна руда",  1.0,  5),
        ]
        for item in items:
            self.hero.pick_up(item)
        for i, item in enumerate(items[:4]):
            self.hero.inventory.assign_quick_slot(item, i)


# ============================================================
#  ДІАЛОГ ДОДАВАННЯ ПРЕДМЕТА
# ============================================================
class AddItemDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Додати предмет")
        self.configure(bg=BG2)
        self.resizable(False, False)
        self.grab_set()
        self.result_item: Optional[Item] = None

        # ── Використовуємо grid щоб кнопки завжди були видні ──
        self.columnconfigure(1, weight=1)

        self._type_var   = tk.StringVar(value="Weapon")
        self._slot_var   = tk.StringVar(value="BODY")
        self._name_var   = tk.StringVar(value="Новий предмет")
        self._weight_var = tk.DoubleVar(value=1.0)
        self._stat_var   = tk.IntVar(value=10)

        def lbl(text, r):
            tk.Label(self, text=text, bg=BG2, fg=TEXT_DIM,
                     font=("Segoe UI", 10), anchor="w").grid(
                row=r, column=0, padx=(16,8), pady=8, sticky="w")

        # Рядок 0 — Тип
        lbl("Тип:", 0)
        type_cb = ttk.Combobox(self, textvariable=self._type_var,
                                values=["Weapon","Armor","Consumable","Resource"],
                                state="readonly", width=22, font=("Segoe UI", 10))
        type_cb.grid(row=0, column=1, padx=(0,16), pady=8, sticky="ew")

        # Рядок 1 — Назва
        lbl("Назва:", 1)
        tk.Entry(self, textvariable=self._name_var, bg=BG3, fg=TEXT,
                 insertbackground=TEXT, font=("Segoe UI", 10), width=24).grid(
            row=1, column=1, padx=(0,16), pady=8, sticky="ew")

        # Рядок 2 — Вага
        lbl("Вага (кг):", 2)
        tk.Spinbox(self, textvariable=self._weight_var,
                   from_=0.1, to=20, increment=0.1, format="%.1f",
                   bg=BG3, fg=TEXT, font=("Segoe UI", 10), width=10).grid(
            row=2, column=1, padx=(0,16), pady=8, sticky="w")

        # Рядок 3 — Стат
        lbl("Стат:", 3)
        tk.Spinbox(self, textvariable=self._stat_var,
                   from_=1, to=200, bg=BG3, fg=TEXT,
                   font=("Segoe UI", 10), width=10).grid(
            row=3, column=1, padx=(0,16), pady=8, sticky="w")
        tk.Label(self, text="(damage / defense / heal / кількість)",
                 bg=BG2, fg=TEXT_DIM, font=("Segoe UI", 8)).grid(
            row=4, column=0, columnspan=2, padx=16, sticky="w")

        # Рядок 5 — Слот броні
        lbl("Слот броні:", 5)
        ttk.Combobox(self, textvariable=self._slot_var,
                     values=["BODY","HEAD","LEGS"],
                     state="readonly", width=22,
                     font=("Segoe UI", 10)).grid(
            row=5, column=1, padx=(0,16), pady=8, sticky="ew")

        # Роздільник
        tk.Frame(self, bg=BORDER, height=1).grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=16, pady=(4,0))

        # Рядок 7 — Кнопки
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

        # Центруємо вікно відносно батьківського
        self.update_idletasks()
        pw = master.winfo_x() + master.winfo_width() // 2
        ph = master.winfo_y() + master.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{pw - w//2}+{ph - h//2}")

    def _create(self):
        name   = self._name_var.get().strip() or "Предмет"
        weight = float(self._weight_var.get())
        stat   = int(self._stat_var.get())
        t = self._type_var.get()
        if t == "Weapon":
            self.result_item = Weapon(name, weight, stat, 1.5)
        elif t == "Armor":
            slot = EquipSlot[self._slot_var.get()]
            self.result_item = Armor(name, weight, stat, slot)
        elif t == "Consumable":
            self.result_item = Consumable(name, weight, stat, 0, "ефект")
        else:
            self.result_item = Resource(name, weight, stat)
        self.destroy()


# ============================================================
#  ДІАЛОГ ЗНЯТИ СПОРЯДЖЕННЯ
# ============================================================
class UnequipDialog(tk.Toplevel):
    def __init__(self, master, equipped: list):
        super().__init__(master)
        self.title("Зняти спорядження")
        self.geometry("280x220")
        self.configure(bg=BG2)
        self.grab_set()
        self.chosen_slot: Optional[EquipSlot] = None

        tk.Label(self, text="Оберіть слот для зняття:", bg=BG2, fg=TEXT,
                 font=("Segoe UI", 10)).pack(pady=10)

        for slot, item in equipped:
            tk.Button(
                self, text=f"{slot.value}: {item.name}",
                bg=BG3, fg=TEXT, relief="flat", padx=10, pady=6,
                cursor="hand2",
                command=lambda s=slot: self._choose(s)
            ).pack(fill="x", padx=20, pady=2)

        tk.Button(self, text="Скасувати", bg="#6a2a2a", fg=TEXT,
                  relief="flat", padx=10, pady=6,
                  command=self.destroy).pack(pady=8)

    def _choose(self, slot):
        self.chosen_slot = slot
        self.destroy()


# ============================================================
#  ДІАЛОГ ПРИЗНАЧЕННЯ ШВИДКОГО СЛОТУ
# ============================================================
class AssignQuickSlotDialog(tk.Toplevel):
    def __init__(self, master, items: list[Item], slot_idx: int):
        super().__init__(master)
        self.title(f"Призначити у слот [{slot_idx+1}]")
        self.geometry("280x300")
        self.configure(bg=BG2)
        self.grab_set()
        self.chosen_item: Optional[Item] = None

        tk.Label(self, text="Оберіть предмет:", bg=BG2, fg=TEXT,
                 font=("Segoe UI", 10)).pack(pady=8)

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
        self._lb = lb

        tk.Button(self, text="✔ Призначити", bg="#2a5a8a", fg=TEXT,
                  relief="flat", padx=10, pady=6,
                  command=self._choose).pack(pady=6)

    def _choose(self):
        sel = self._lb.curselection()
        if sel:
            self.chosen_item = self._items[sel[0]]
        self.destroy()


# ============================================================
#  ЗАПУСК
# ============================================================
if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()