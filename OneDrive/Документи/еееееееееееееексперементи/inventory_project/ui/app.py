from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from typing import Optional
from datetime import datetime

from models.items import Item, Weapon, Armor, Consumable, Resource
from models.enums import ItemType, EquipSlot
from core.observer import IInventoryObserver
from core.character import Character
from utils.theme import (
    BG, BG2, BG3, ACCENT, ACCENT2, GREEN, RED, ORANGE,
    TEXT, TEXT_DIM, BORDER, CELL_SIZE, ITEM_COLORS, ITEM_ICONS,
)
from ui.dialogs import AddItemDialog, UnequipDialog, AssignQuickSlotDialog


class InventoryApp(tk.Tk, IInventoryObserver):
    """Головне вікно програми — Observer підписник."""

    def __init__(self):
        super().__init__()
        self.title("⚔  Система Інвентарю")
        self.geometry("1180x720")
        self.minsize(1000, 650)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.hero = Character("Артем", 120)
        self.hero.inventory.subscribe(self)

        self._selected_item: Optional[Item] = None
        self._hover_cell: tuple[int, int]   = (-1, -1)
        self._grid_rows = 8
        self._grid_cols = 6

        self._build_ui()
        self._seed_items()
        self._refresh_all()

    # ── Observer ──────────────────────────────────────────────
    def on_inventory_changed(self, message: str) -> None:
        self._log(message)
        self._refresh_all()

    # ──────────────────────────────────────────────────────────
    #  ПОБУДОВА UI
    # ──────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        self._build_topbar()
        self._build_bottombar()

        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=6, pady=4)

        left = tk.Frame(main, bg=BG, width=190)
        left.pack(side="left", fill="y", padx=(0, 4))
        left.pack_propagate(False)
        self._build_quick_slots(left)
        self._build_log(left)

        center = tk.Frame(main, bg=BG)
        center.pack(side="left", fill="both", expand=True, padx=4)
        self._build_grid(center)

        right = tk.Frame(main, bg=BG, width=270)
        right.pack(side="left", fill="y", padx=(4, 0))
        right.pack_propagate(False)
        self._build_equipment_panel(right)
        self._build_sections_panel(right)

    def _build_topbar(self) -> None:
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

    def _build_bottombar(self) -> None:
        bot = tk.Frame(self, bg=BG2, height=46)
        bot.pack(fill="x", side="bottom")
        bot.pack_propagate(False)

        buttons = [
            ("➕ Додати предмет",   "#2a6a3a", self._dialog_add_item),
            ("▶ Використати",       "#2a3a7a", self._use_selected),
            ("⚔ Екіпірувати",       "#5a3a10", self._equip_selected),
            ("↩ Зняти спорядження", "#3a2a5a", self._dialog_unequip),
            ("🗑 Викинути",          "#6a1a1a", self._drop_selected),
            ("💔 Отримати удар −20","#7a3a10", self._take_hit),
        ]
        for txt, color, cmd in buttons:
            tk.Button(bot, text=txt, bg=color, fg=TEXT, relief="flat",
                      font=("Segoe UI", 9), padx=10, pady=6, cursor="hand2",
                      activebackground=ACCENT, activeforeground="white",
                      command=cmd).pack(side="left", padx=4, pady=6)

    def _build_quick_slots(self, parent: tk.Frame) -> None:
        frame = self._panel(parent, "⚡ ШВИДКІ СЛОТИ")
        frame.pack(fill="x", pady=(0, 4))

        self._qs_btns: list[tk.Button] = []
        for i in range(4):
            btn = tk.Button(
                frame, text=f"[{i + 1}]  —", bg=BG3, fg=TEXT_DIM,
                relief="flat", font=("Segoe UI", 9), anchor="w", padx=8,
                cursor="hand2", activebackground=ACCENT,
                command=lambda idx=i: self._use_quick_slot(idx)
            )
            btn.pack(fill="x", padx=6, pady=2, ipady=6)
            btn.bind("<Button-3>", lambda e, idx=i: self._qs_context(e, idx))
            self._qs_btns.append(btn)

    def _build_log(self, parent: tk.Frame) -> None:
        frame = self._panel(parent, "📋 ЛОГ ПОДІЙ")
        frame.pack(fill="both", expand=True)

        self._log_text = tk.Text(
            frame, bg="#0e0e18", fg=TEXT_DIM, relief="flat",
            font=("Consolas", 8), wrap="word", state="disabled", cursor="arrow"
        )
        sb = tk.Scrollbar(frame, command=self._log_text.yview, bg=BG3)
        self._log_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._log_text.pack(fill="both", expand=True, padx=4, pady=4)

    def _build_grid(self, parent: tk.Frame) -> None:
        self._panel_header(parent, "🎒 ІНВЕНТАР  (клік — вибір, ПКМ — меню)").pack(fill="x")
        tk.Label(parent, text="Подвійний клік → екіпірувати/використати",
                 bg=BG, fg=TEXT_DIM, font=("Segoe UI", 8)).pack()

        canvas_frame = tk.Frame(parent, bg=BG)
        canvas_frame.pack(fill="both", expand=True, padx=4, pady=4)

        w = self._grid_cols * CELL_SIZE + 2
        h = self._grid_rows * CELL_SIZE + 2
        self._canvas = tk.Canvas(canvas_frame, width=w, height=h,
                                  bg="#0e0e18", highlightthickness=1,
                                  highlightbackground=BORDER)
        self._canvas.pack(anchor="nw")
        self._canvas.bind("<Button-1>",       self._grid_click)
        self._canvas.bind("<Double-Button-1>", self._grid_dbl_click)
        self._canvas.bind("<Button-3>",        self._grid_rclick)
        self._canvas.bind("<Motion>",          self._grid_hover)

    def _build_equipment_panel(self, parent: tk.Frame) -> None:
        frame = self._panel(parent, "🛡 СПОРЯДЖЕННЯ")
        frame.pack(fill="x", pady=(0, 4))

        self._equip_labels: dict[EquipSlot, tk.Label] = {}
        for slot, label in [
            (EquipSlot.WEAPON, "⚔ Зброя"),
            (EquipSlot.HEAD,   "🪖 Голова"),
            (EquipSlot.BODY,   "🥋 Тіло"),
            (EquipSlot.LEGS,   "👢 Ноги"),
        ]:
            row = tk.Frame(frame, bg=BG3)
            row.pack(fill="x", padx=6, pady=2)
            tk.Label(row, text=label, bg=BG3, fg=TEXT_DIM,
                     font=("Segoe UI", 9), width=9, anchor="w").pack(side="left", padx=4)
            lbl = tk.Label(row, text="—", bg="#1a1a2e", fg=TEXT_DIM,
                           font=("Segoe UI", 9), anchor="w", padx=6,
                           relief="flat", bd=1, cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=2, ipady=4)
            lbl.bind("<Double-Button-1>", lambda e, s=slot: self._unequip_slot(s))
            self._equip_labels[slot] = lbl

        self._lbl_bonuses = tk.Label(frame, text="", bg=BG3, fg=ACCENT2, font=("Segoe UI", 9))
        self._lbl_bonuses.pack(pady=(4, 6))

    def _build_sections_panel(self, parent: tk.Frame) -> None:
        outer = self._panel(parent, "📦 ПРЕДМЕТИ ЗА ТИПОМ")
        outer.pack(fill="both", expand=True)

        scroll_canvas = tk.Canvas(outer, bg=BG2, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        scroll_canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(scroll_canvas, bg=BG2)
        win = scroll_canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: (
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")),
            scroll_canvas.itemconfig(win, width=scroll_canvas.winfo_width())
        ))
        scroll_canvas.bind("<Configure>",
                           lambda e: scroll_canvas.itemconfig(win, width=e.width))

        self._section_frames: dict[ItemType, tk.Frame]  = {}
        self._section_hdrs:   dict[ItemType, tk.Button] = {}
        self._section_open:   dict[ItemType, bool]      = {t: True for t in ItemType}

        for itype in ItemType:
            box = tk.Frame(inner, bg=BG2)
            box.pack(fill="x", pady=(4, 0))

            hdr = tk.Button(
                box, text=f"{ITEM_ICONS[itype]} {itype.value}  ▼",
                bg="#2a3a5a", fg="#a0c0ff", relief="flat",
                font=("Segoe UI", 9, "bold"), anchor="w", padx=8,
                cursor="hand2", command=lambda t=itype: self._toggle_section(t)
            )
            hdr.pack(fill="x")

            content = tk.Frame(box, bg=BG2)
            content.pack(fill="x")

            self._section_frames[itype] = content
            self._section_hdrs[itype]   = hdr

    # ──────────────────────────────────────────────────────────
    #  МАЛЮВАННЯ СІТКИ
    # ──────────────────────────────────────────────────────────
    def _draw_grid(self) -> None:
        c = self._canvas
        c.delete("all")

        for r in range(self._grid_rows):
            for col in range(self._grid_cols):
                x1 = col * CELL_SIZE + 1
                y1 = r   * CELL_SIZE + 1
                x2 = x1 + CELL_SIZE - 1
                y2 = y1 + CELL_SIZE - 1
                hover = (r, col) == self._hover_cell
                c.create_rectangle(x1, y1, x2, y2,
                                   fill="#222240" if hover else "#181828",
                                   outline=BORDER, width=1)

        drawn: set[int] = set()
        for item in self.hero.inventory.items:
            if id(item) in drawn or item.grid_x < 0:
                continue
            drawn.add(id(item))

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
            c.create_text(x2-4, y1+4, text=ITEM_ICONS.get(item.item_type, "?"),
                          fill=border_color, font=("Segoe UI", 9), anchor="ne")

    # ──────────────────────────────────────────────────────────
    #  ОНОВЛЕННЯ UI
    # ──────────────────────────────────────────────────────────
    def _refresh_all(self) -> None:
        self._refresh_topbar()
        self._refresh_equipment()
        self._refresh_sections()
        self._refresh_quick_slots()
        self._draw_grid()

    def _refresh_topbar(self) -> None:
        h = self.hero
        self._lbl_hp.config(
            text=f"❤  HP: {h.hp} / {h.max_hp}",
            fg=RED if h.hp < 40 else GREEN)
        self._lbl_stats.config(
            text=f"⚔ Атака: {h.equipment.get_attack_bonus()}  │  🛡 Захист: {h.equipment.get_defense_bonus()}")
        w = h.inventory.current_weight
        self._lbl_weight.config(
            text=f"⚖  {w:.1f} / 25.0 кг",
            fg=RED if w > 22 else ORANGE)

    def _refresh_equipment(self) -> None:
        for slot, lbl in self._equip_labels.items():
            item = self.hero.equipment.get_item(slot)
            if item:
                _, bc = ITEM_COLORS.get(item.item_type, ("#333", "#aaa"))
                lbl.config(text=f"  {item.name}", fg=bc)
            else:
                lbl.config(text="  —", fg=TEXT_DIM)
        self._lbl_bonuses.config(
            text=f"Атака: +{self.hero.equipment.get_attack_bonus()}"
                 f"  │  Захист: +{self.hero.equipment.get_defense_bonus()}")

    def _refresh_sections(self) -> None:
        for itype, frame in self._section_frames.items():
            for w in frame.winfo_children():
                w.destroy()
            if not self._section_open[itype]:
                frame.pack_forget()
                continue
            frame.pack(fill="x")

            items = [i for i in self.hero.inventory.items if i.item_type == itype]
            if not items:
                tk.Label(frame, text="  (порожньо)", bg=BG2, fg=TEXT_DIM,
                         font=("Segoe UI", 8)).pack(anchor="w", padx=8, pady=2)
            for item in items:
                sel = item is self._selected_item
                _, bc = ITEM_COLORS.get(item.item_type, ("#333", "#aaa"))
                btn = tk.Button(
                    frame,
                    text=f"  {item.name}  ({item.weight}кг)",
                    bg="#2a3a5a" if sel else "#1e2035",
                    fg=bc if sel else TEXT,
                    relief="flat", font=("Segoe UI", 9), anchor="w",
                    cursor="hand2",
                    command=lambda i=item: self._select_item(i)
                )
                btn.pack(fill="x", padx=4, pady=1, ipady=3)
                btn.bind("<Button-3>",       lambda e, i=item: self._item_context(e, i))
                btn.bind("<Double-Button-1>", lambda e, i=item: self._quick_action(i))

    def _refresh_quick_slots(self) -> None:
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
    def _grid_coords(self, event: tk.Event) -> tuple[int, int]:
        return event.y // CELL_SIZE, event.x // CELL_SIZE

    def _grid_click(self, event: tk.Event) -> None:
        r, c = self._grid_coords(event)
        self._select_item(self.hero.inventory.get_item_at_grid(r, c))

    def _grid_dbl_click(self, event: tk.Event) -> None:
        r, c = self._grid_coords(event)
        item = self.hero.inventory.get_item_at_grid(r, c)
        if item:
            self._quick_action(item)

    def _grid_rclick(self, event: tk.Event) -> None:
        r, c = self._grid_coords(event)
        item = self.hero.inventory.get_item_at_grid(r, c)
        if item:
            self._item_context(event, item)

    def _grid_hover(self, event: tk.Event) -> None:
        cell = (event.y // CELL_SIZE, event.x // CELL_SIZE)
        if cell != self._hover_cell:
            self._hover_cell = cell
            self._draw_grid()

    # ──────────────────────────────────────────────────────────
    #  ДІЇ З ПРЕДМЕТАМИ
    # ──────────────────────────────────────────────────────────
    def _select_item(self, item: Optional[Item]) -> None:
        self._selected_item = item
        self._draw_grid()
        self._refresh_sections()
        if item:
            self._log(f"🔍 Обрано: {item}")

    def _quick_action(self, item: Item) -> None:
        if isinstance(item, Consumable):
            msg = self.hero.use_item(item)
            self._log(f"💊 {msg}")
        elif isinstance(item, (Weapon, Armor)):
            self._equip_item(item)
        else:
            self._log(self.hero.use_item(item))
        self._refresh_all()

    def _use_selected(self) -> None:
        if not self._selected_item:
            messagebox.showinfo("Увага", "Спочатку оберіть предмет")
            return
        self._log(f"▶ {self.hero.use_item(self._selected_item)}")
        self._selected_item = None
        self._refresh_all()

    def _equip_selected(self) -> None:
        item = self._selected_item
        if not item:
            messagebox.showinfo("Увага", "Спочатку оберіть предмет")
            return
        self._equip_item(item)

    def _equip_item(self, item: Item) -> None:
        if isinstance(item, Weapon):
            ok, msg = self.hero.equip_item(item, EquipSlot.WEAPON)
        elif isinstance(item, Armor):
            ok, msg = self.hero.equip_item(item, item.slot)
        else:
            ok, msg = False, "Не можна екіпірувати"
        self._log(("✅ " if ok else "❌ ") + msg)
        self._refresh_all()

    def _drop_selected(self) -> None:
        item = self._selected_item
        if not item:
            messagebox.showinfo("Увага", "Спочатку оберіть предмет")
            return
        if messagebox.askyesno("Підтвердження", f"Викинути «{item.name}»?"):
            self.hero.inventory.remove_item(item)
            self._selected_item = None
            self._refresh_all()

    def _unequip_slot(self, slot: EquipSlot) -> None:
        ok, msg = self.hero.unequip_item(slot)
        self._log(("✅ " if ok else "❌ ") + msg)
        self._refresh_all()

    def _dialog_unequip(self) -> None:
        equipped = [(s, self.hero.equipment.get_item(s))
                    for s in EquipSlot if s != EquipSlot.NONE
                    and self.hero.equipment.get_item(s)]
        if not equipped:
            messagebox.showinfo("Увага", "Немає екіпірованих предметів")
            return
        dlg = UnequipDialog(self, equipped)  # type: ignore[arg-type]
        self.wait_window(dlg)
        if dlg.chosen_slot:
            self._unequip_slot(dlg.chosen_slot)

    def _take_hit(self) -> None:
        self.hero.take_damage(20)
        self._log(f"💔 Отримано 20 пошкодження. HP = {self.hero.hp}/{self.hero.max_hp}")
        self._refresh_all()

    def _use_quick_slot(self, idx: int) -> None:
        item = self.hero.inventory.get_quick_slot(idx)
        if not item:
            self._log(f"⚡ Швидкий слот [{idx+1}] порожній")
            return
        self._quick_action(item)

    def _qs_context(self, event: tk.Event, idx: int) -> None:
        item = self.hero.inventory.get_quick_slot(idx)
        menu = tk.Menu(self, tearoff=0, bg=BG3, fg=TEXT)
        if item:
            menu.add_command(label=f"▶ Використати «{item.name}»",
                             command=lambda: self._use_quick_slot(idx))
            menu.add_separator()
            menu.add_command(label="✖ Очистити слот",
                             command=lambda: (
                                 self.hero.inventory.clear_quick_slot(idx),
                                 self._refresh_quick_slots()))
        else:
            if self.hero.inventory.items:
                menu.add_command(label="Призначити предмет...",
                                 command=lambda: self._dialog_assign_qs(idx))
            else:
                menu.add_command(label="Інвентар порожній", state="disabled")
        menu.post(event.x_root, event.y_root)

    def _dialog_assign_qs(self, idx: int) -> None:
        dlg = AssignQuickSlotDialog(self, self.hero.inventory.items, idx)
        self.wait_window(dlg)
        if dlg.chosen_item:
            self.hero.inventory.assign_quick_slot(dlg.chosen_item, idx)
            self._refresh_quick_slots()

    def _item_context(self, event: tk.Event, item: Item) -> None:
        menu = tk.Menu(self, tearoff=0, bg=BG3, fg=TEXT,
                       activebackground=ACCENT, activeforeground="white")
        menu.add_command(label=f"🔍 {item.name}  ({item.weight}кг)",
                         state="disabled", font=("Segoe UI", 9, "bold"))
        menu.add_separator()
        menu.add_command(label="▶ Використати",
                         command=lambda: (setattr(self, "_selected_item", item),
                                          self._use_selected()))
        if isinstance(item, (Weapon, Armor)):
            menu.add_command(label="⚔ Екіпірувати",
                             command=lambda: self._equip_item(item))
        menu.add_separator()
        for i in range(4):
            menu.add_command(label=f"⚡ Призначити у слот [{i+1}]",
                             command=lambda i=i: (
                                 self.hero.inventory.assign_quick_slot(item, i),
                                 self._refresh_quick_slots()))
        menu.add_separator()
        menu.add_command(label="🗑 Викинути",
                         command=lambda: (
                             messagebox.askyesno("Підтвердження",
                                                  f"Викинути «{item.name}»?") and (
                                 self.hero.inventory.remove_item(item),
                                 setattr(self, "_selected_item", None),
                                 self._refresh_all()
                             )))
        menu.post(event.x_root, event.y_root)

    def _toggle_section(self, itype: ItemType) -> None:
        self._section_open[itype] = not self._section_open[itype]
        icon = "▼" if self._section_open[itype] else "▶"
        self._section_hdrs[itype].config(
            text=f"{ITEM_ICONS[itype]} {itype.value}  {icon}")
        self._refresh_sections()

    def _dialog_add_item(self) -> None:
        dlg = AddItemDialog(self)
        self.wait_window(dlg)
        if dlg.result_item:
            ok = self.hero.pick_up(dlg.result_item)
            if ok:
                for i in range(4):
                    if self.hero.inventory.get_quick_slot(i) is None:
                        self.hero.inventory.assign_quick_slot(dlg.result_item, i)
                        break
            self._refresh_all()

    # ──────────────────────────────────────────────────────────
    #  ДОПОМІЖНІ
    # ──────────────────────────────────────────────────────────
    def _log(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_text.configure(state="normal")
        self._log_text.insert("end", f"{ts}  {msg}\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    @staticmethod
    def _panel(parent: tk.Frame, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        tk.Label(outer, text=title, bg="#1e1e30", fg=ACCENT,
                 font=("Segoe UI", 9, "bold"), anchor="w",
                 padx=8, pady=4).pack(fill="x")
        return outer

    @staticmethod
    def _panel_header(parent: tk.Frame, title: str) -> tk.Frame:
        f = tk.Frame(parent, bg=BG2)
        tk.Label(f, text=title, bg=BG2, fg=ACCENT,
                 font=("Segoe UI", 9, "bold"), anchor="w",
                 padx=8, pady=4).pack(fill="x")
        return f

    def _seed_items(self) -> None:
        items: list[Item] = [
            Weapon("Сталевий меч",    3.5, 25, 1.5),
            Weapon("Ельфійський лук", 2.0, 18, 30.0),
            Armor("Нагрудник лицаря", 8.0, 30, EquipSlot.BODY),
            Armor("Шолом варвара",    3.0, 15, EquipSlot.HEAD),
            Consumable("Мале зілля",  0.3, 30, 0, "миттєве зцілення"),
            Consumable("Велике зілля",0.5, 80, 5, "регенерація"),
            Resource("Дерево",        0.5, 10),
            Resource("Залізна руда",  1.0,  5),
        ]
        for item in items:
            self.hero.pick_up(item)
        for i, item in enumerate(items[:4]):
            self.hero.inventory.assign_quick_slot(item, i)
