from models.enums import ItemType

# ── Кольори фону ──────────────────────────────────────────
BG       = "#12121a"
BG2      = "#1a1a26"
BG3      = "#22223a"

# ── Акценти ───────────────────────────────────────────────
ACCENT   = "#4a90d9"
ACCENT2  = "#f0c040"
GREEN    = "#4caf80"
RED      = "#e05050"
ORANGE   = "#e08030"

# ── Текст ─────────────────────────────────────────────────
TEXT     = "#e8e8f0"
TEXT_DIM = "#808090"
BORDER   = "#303050"

# ── Розмір клітинки сітки ─────────────────────────────────
CELL_SIZE = 52

# ── Кольори предметів (фон, рамка) ────────────────────────
ITEM_COLORS: dict[ItemType, tuple[str, str]] = {
    ItemType.WEAPON:     ("#7a3a10", "#e0943a"),
    ItemType.ARMOR:      ("#1a3a6a", "#4a90d9"),
    ItemType.CONSUMABLE: ("#1a5a30", "#50c878"),
    ItemType.RESOURCE:   ("#3a2a5a", "#9070d0"),
}

# ── Іконки типів ──────────────────────────────────────────
ITEM_ICONS: dict[ItemType, str] = {
    ItemType.WEAPON:     "⚔",
    ItemType.ARMOR:      "🛡",
    ItemType.CONSUMABLE: "🧪",
    ItemType.RESOURCE:   "📦",
}
