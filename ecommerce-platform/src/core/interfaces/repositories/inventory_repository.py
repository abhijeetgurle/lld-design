from abc import ABC, abstractmethod
from typing import Optional, List

from core.entities.inventory import InventoryItem, InventoryReservation, Warehouse


class InventoryRepository(ABC):
    """Repository interface for inventory data access"""

    @abstractmethod
    def save_inventory_item(self, item: InventoryItem) -> InventoryItem:
        pass

    @abstractmethod
    def find_inventory_item(self, product_id: str, warehouse_id: str) -> Optional[InventoryItem]:
        pass

    @abstractmethod
    def find_inventory_by_product(self, product_id: str) -> List[InventoryItem]:
        pass

    @abstractmethod
    def find_inventory_by_warehouse(self, warehouse_id: str) -> List[InventoryItem]:
        pass

    @abstractmethod
    def save_reservation(self, reservation: InventoryReservation) -> InventoryReservation:
        pass

    @abstractmethod
    def find_reservation(self, reservation_id: str) -> Optional[InventoryReservation]:
        pass

    @abstractmethod
    def find_active_reservations(self) -> List[InventoryReservation]:
        pass

    @abstractmethod
    def save_warehouse(self, warehouse: Warehouse) -> Warehouse:
        pass

    @abstractmethod
    def find_warehouse(self, warehouse_id: str) -> Optional[Warehouse]:
        pass

    @abstractmethod
    def find_active_warehouses(self) -> List[Warehouse]:
        pass