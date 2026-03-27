from enum import Enum


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
