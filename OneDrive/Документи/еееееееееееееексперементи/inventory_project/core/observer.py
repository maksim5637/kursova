from abc import ABC, abstractmethod


class IInventoryObserver(ABC):
    """Інтерфейс патерну Observer."""

    @abstractmethod
    def on_inventory_changed(self, message: str) -> None: ...
