# Система Інвентарю

Проєкт реалізує систему інвентарю персонажа з графічним інтерфейсом на Tkinter.

## Запуск

```bash
python3 main.py
```

Залежності: лише стандартна бібліотека Python (tkinter вбудований).

## Структура проєкту

```
inventory_project/
│
├── main.py                  # Точка входу
│
├── models/                  # Моделі даних
│   ├── __init__.py
│   ├── enums.py             # ItemType, EquipSlot
│   └── items.py             # Item, Weapon, Armor, Consumable, Resource
│
├── core/                    # Бізнес-логіка
│   ├── __init__.py
│   ├── observer.py          # Інтерфейс IInventoryObserver
│   ├── grid.py              # InventoryGrid, GridCell (Composite)
│   ├── inventory.py         # Клас Inventory
│   ├── equipment.py         # Клас Equipment (Strategy)
│   └── character.py         # Клас Character (координатор)
│
├── ui/                      # Графічний інтерфейс
│   ├── __init__.py
│   ├── app.py               # Головне вікно InventoryApp
│   └── dialogs/
│       ├── __init__.py
│       ├── add_item.py      # Діалог додавання предмета
│       └── other_dialogs.py # UnequipDialog, AssignQuickSlotDialog
│
└── utils/                   # Допоміжні утиліти
    ├── __init__.py
    └── theme.py             # Кольори, стилі, константи
```

## Патерни проектування

| Патерн        | Де використовується                          |
|---------------|----------------------------------------------|
| Observer      | `Inventory` → `InventoryApp`                 |
| Factory Method| `Item` + підкласи (`Weapon`, `Armor`, ...)   |
| Strategy      | `Equipment._compatible()`                    |
| Composite     | `InventoryGrid` + `GridCell`                 |
