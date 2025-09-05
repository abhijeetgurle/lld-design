from threading import Lock
from typing import Dict, Optional, List

from core.entities.inventory import InventoryItem, InventoryReservation, Warehouse, ReservationStatus
from core.interfaces.repositories.inventory_repository import InventoryRepository


class InMemoryInventoryRepository(InventoryRepository):
    """In-memory implementation for testing and demos"""

    def __init__(self):
        self._inventory_items: Dict[str, InventoryItem] = {}  # "{product_id}_{warehouse_id}" -> InventoryItem
        self._reservations: Dict[str, InventoryReservation] = {}
        self._warehouses: Dict[str, Warehouse] = {}
        self._lock = Lock()

    def save_inventory_item(self, item: InventoryItem) -> InventoryItem:
        with self._lock:
            key = f"{item.product_id}_{item.warehouse_id}"
            self._inventory_items[key] = item
            return item

    def find_inventory_item(self, product_id: str, warehouse_id: str) -> Optional[InventoryItem]:
        key = f"{product_id}_{warehouse_id}"
        return self._inventory_items.get(key)

    def find_inventory_by_product(self, product_id: str) -> List[InventoryItem]:
        return [
            item for item in self._inventory_items.values()
            if item.product_id == product_id
        ]

    def find_inventory_by_warehouse(self, warehouse_id: str) -> List[InventoryItem]:
        return [
            item for item in self._inventory_items.values()
            if item.warehouse_id == warehouse_id
        ]

    def save_reservation(self, reservation: InventoryReservation) -> InventoryReservation:
        with self._lock:
            self._reservations[reservation.reservation_id] = reservation
            return reservation

    def find_reservation(self, reservation_id: str) -> Optional[InventoryReservation]:
        return self._reservations.get(reservation_id)

    def find_active_reservations(self) -> List[InventoryReservation]:
        return [
            res for res in self._reservations.values()
            if res.status == ReservationStatus.ACTIVE
        ]

    def save_warehouse(self, warehouse: Warehouse) -> Warehouse:
        with self._lock:
            self._warehouses[warehouse.warehouse_id] = warehouse
            return warehouse

    def find_warehouse(self, warehouse_id: str) -> Optional[Warehouse]:
        return self._warehouses.get(warehouse_id)

    def find_active_warehouses(self) -> List[Warehouse]:
        return [
            warehouse for warehouse in self._warehouses.values()
            if warehouse.is_active
        ]