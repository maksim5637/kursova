"""
╔════════════════════════════════════════╗
║     СИСТЕМА ІНВЕНТАРЮ — Запуск         ║
╚════════════════════════════════════════╝
Запуск: python3 main.py
"""
from ui.app import InventoryApp


if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
