import threading
import uuid
from threading import Lock
from typing import List, Dict, Optional, Tuple

from core.entities.cart import CartItem
from core.entities.inventory import Warehouse, InventoryItem, InventoryReservation, ReservationStatus
from core.entities.order import OrderItem
from core.interfaces.repositories.inventory_repository import InventoryRepository


class InventoryServiceException(Exception):
    """Base exception for inventory service"""
    pass


class InsufficientInventoryException(InventoryServiceException):
    """Exception when inventory is insufficient"""
    pass


class ReservationException(InventoryServiceException):
    """Exception during reservation operations"""
    pass


class InventoryService:
    """
    Complete inventory management service

    Responsibilities:
    1. Multi-warehouse inventory tracking
    2. Reservation system (prevents overselling)
    3. Thread-safe operations for concurrent access
    4. Automatic cleanup of expired reservations
    5. Low stock monitoring and alerts
    6. Inventory allocation optimization
    """

    def __init__(self,
                 inventory_repository: InventoryRepository,
                 notification_service=None):
        self.inventory_repo = inventory_repository
        self.notification_service = notification_service

        # Configuration
        self.default_reservation_expiry_minutes = 15
        self.low_stock_threshold = 10
        self.cleanup_interval_minutes = 5

        # Thread safety for service-level operations
        self._service_lock = Lock()

        # Background cleanup
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        self._start_background_cleanup()

    def add_warehouse(self, name: str, location: str, max_capacity: int = None) -> Warehouse:
        """Add a new warehouse to the system"""
        warehouse = Warehouse(
            warehouse_id=str(uuid.uuid4()),
            name=name,
            location=location,
            max_capacity=max_capacity
        )

        saved_warehouse = self.inventory_repo.save_warehouse(warehouse)
        print(f"Added warehouse {saved_warehouse.warehouse_id}: {name} at {location}")

        return saved_warehouse

    def add_inventory(self, product_id: str, warehouse_id: str, quantity: int) -> InventoryItem:
        """
        Add inventory to a specific warehouse

        Creates new inventory item or updates existing one
        """
        if quantity <= 0:
            raise ValueError("Inventory quantity must be positive")

        # Check if warehouse exists and is active
        warehouse = self.inventory_repo.find_warehouse(warehouse_id)
        if not warehouse or not warehouse.is_active:
            raise InventoryServiceException(f"Warehouse {warehouse_id} not available")

        # Get or create inventory item
        inventory_item = self.inventory_repo.find_inventory_item(product_id, warehouse_id)

        if inventory_item:
            # Update existing inventory
            inventory_item.add_stock(quantity)
        else:
            # Create new inventory item
            inventory_item = InventoryItem(
                product_id=product_id,
                warehouse_id=warehouse_id,
                available_quantity=quantity,
                total_received=quantity
            )

        saved_item = self.inventory_repo.save_inventory_item(inventory_item)

        print(f"Added {quantity} units of {product_id} to warehouse {warehouse_id}")
        return saved_item

    def get_available_quantity(self, product_id: str, warehouse_id: str = None) -> int:
        """
        Get available quantity for a product

        If warehouse_id is None, returns total across all warehouses
        """
        if warehouse_id:
            # Specific warehouse
            inventory_item = self.inventory_repo.find_inventory_item(product_id, warehouse_id)
            return inventory_item.available_quantity if inventory_item else 0
        else:
            # All warehouses
            inventory_items = self.inventory_repo.find_inventory_by_product(product_id)
            return sum(item.available_quantity for item in inventory_items)

    def check_availability(self, cart_items: List[CartItem]) -> bool:
        """
        Check if all items in cart are available across all warehouses

        This is the method called by OrderService
        """
        for cart_item in cart_items:
            available = self.get_available_quantity(cart_item.product_id)
            if available < cart_item.quantity:
                print(f"Insufficient inventory for {cart_item.product_id}: "
                               f"needed {cart_item.quantity}, available {available}")
                return False

        return True

    def reserve_items(self, cart_items: List[CartItem], customer_id: str) -> str:
        """
        Reserve inventory for cart items

        Algorithm:
        1. Find optimal warehouse allocation for each product
        2. Reserve inventory atomically across warehouses
        3. Create reservation record for tracking
        4. Handle rollback if any item cannot be reserved

        Returns reservation_id for tracking
        """
        with self._service_lock:  # Ensure atomic reservation across all items

            # Step 1: Plan allocation across warehouses
            allocation_plan = self._plan_inventory_allocation(cart_items)

            if not allocation_plan:
                raise InsufficientInventoryException("Cannot fulfill cart items")

            # Step 2: Reserve inventory according to plan
            reserved_items = {}
            successfully_reserved = []

            try:
                for (product_id, warehouse_id), quantity in allocation_plan.items():
                    inventory_item = self.inventory_repo.find_inventory_item(product_id, warehouse_id)

                    if not inventory_item or not inventory_item.reserve(quantity):
                        raise InsufficientInventoryException(
                            f"Failed to reserve {quantity} units of {product_id} from {warehouse_id}"
                        )

                    # Save updated inventory
                    self.inventory_repo.save_inventory_item(inventory_item)

                    # Track for rollback if needed
                    successfully_reserved.append((inventory_item, quantity))
                    reserved_items[f"{product_id}_{warehouse_id}"] = quantity

                # Step 3: Create reservation record
                reservation = InventoryReservation.create(
                    customer_id=customer_id,
                    items=reserved_items,
                    expiry_minutes=self.default_reservation_expiry_minutes
                )

                saved_reservation = self.inventory_repo.save_reservation(reservation)

                print(f"Reserved items for customer {customer_id}, "
                            f"reservation_id: {reservation.reservation_id}")

                return reservation.reservation_id

            except Exception as e:
                # Rollback all successful reservations
                self._rollback_reservations(successfully_reserved)
                print(f"Reservation failed for customer {customer_id}: {e}")
                raise ReservationException(f"Reservation failed: {str(e)}")

    def confirm_reservation(self, reservation_id: str) -> bool:
        """
        Confirm reservation (convert reserved inventory to sold)

        Called when payment is successful
        """
        reservation = self.inventory_repo.find_reservation(reservation_id)
        if not reservation:
            raise ReservationException(f"Reservation {reservation_id} not found")

        if not reservation.is_active():
            raise ReservationException(f"Reservation {reservation_id} is not active")

        with self._service_lock:
            try:
                # Confirm inventory items
                for item_key, quantity in reservation.items.items():
                    product_id, warehouse_id = item_key.split('_', 1)

                    inventory_item = self.inventory_repo.find_inventory_item(product_id, warehouse_id)
                    if inventory_item:
                        confirmed_qty = inventory_item.confirm_reservation(quantity)
                        self.inventory_repo.save_inventory_item(inventory_item)

                        if confirmed_qty < quantity:
                            print(f"Only confirmed {confirmed_qty}/{quantity} for {item_key}")

                # Mark reservation as confirmed
                reservation.confirm()
                self.inventory_repo.save_reservation(reservation)

                print(f"Confirmed reservation {reservation_id}")

                # Check for low stock alerts
                self._check_low_stock_alerts()

                return True

            except Exception as e:
                print(f"Failed to confirm reservation {reservation_id}: {e}")
                raise ReservationException(f"Confirmation failed: {str(e)}")

    def cancel_reservation(self, reservation_id: str) -> bool:
        """
        Cancel reservation (return inventory to available)

        Called when payment fails or order is cancelled
        """
        reservation = self.inventory_repo.find_reservation(reservation_id)
        if not reservation:
            print(f"Reservation {reservation_id} not found for cancellation")
            return False

        if reservation.status in [ReservationStatus.CONFIRMED, ReservationStatus.CANCELLED]:
            print(f"Reservation {reservation_id} already {reservation.status}")
            return True

        with self._service_lock:
            try:
                # Release inventory items
                for item_key, quantity in reservation.items.items():
                    product_id, warehouse_id = item_key.split('_', 1)

                    inventory_item = self.inventory_repo.find_inventory_item(product_id, warehouse_id)
                    if inventory_item:
                        released_qty = inventory_item.release_reservation(quantity)
                        self.inventory_repo.save_inventory_item(inventory_item)

                        if released_qty < quantity:
                            print(f"Only released {released_qty}/{quantity} for {item_key}")

                # Mark reservation as cancelled
                reservation.cancel()
                self.inventory_repo.save_reservation(reservation)

                print(f"Cancelled reservation {reservation_id}")
                return True

            except Exception as e:
                print(f"Failed to cancel reservation {reservation_id}: {e}")
                return False

    def restore_items(self, order_items: List[OrderItem]) -> bool:
        """
        Restore inventory from cancelled order

        Used when order is cancelled after payment
        """
        with self._service_lock:
            try:
                for order_item in order_items:
                    # Find best warehouse to restore to (prefer first available)
                    inventory_items = self.inventory_repo.find_inventory_by_product(order_item.product_id)

                    if inventory_items:
                        # Restore to first warehouse (in real system, might use smarter logic)
                        target_item = inventory_items[0]
                        target_item.add_stock(order_item.quantity)
                        self.inventory_repo.save_inventory_item(target_item)
                    else:
                        # Create new inventory item in default warehouse
                        warehouses = self.inventory_repo.find_active_warehouses()
                        if warehouses:
                            new_item = InventoryItem(
                                product_id=order_item.product_id,
                                warehouse_id=warehouses[0].warehouse_id,
                                available_quantity=order_item.quantity,
                                total_received=order_item.quantity
                            )
                            self.inventory_repo.save_inventory_item(new_item)

                print(f"Restored inventory for {len(order_items)} items")
                return True

            except Exception as e:
                print(f"Failed to restore items: {e}")
                return False

    def get_low_stock_products(self) -> List[Dict]:
        """Get products with low stock across all warehouses"""
        low_stock_products = []

        # Get all inventory items
        warehouses = self.inventory_repo.find_active_warehouses()
        for warehouse in warehouses:
            inventory_items = self.inventory_repo.find_inventory_by_warehouse(warehouse.warehouse_id)

            for item in inventory_items:
                if item.is_low_stock(self.low_stock_threshold):
                    low_stock_products.append({
                        'product_id': item.product_id,
                        'warehouse_id': item.warehouse_id,
                        'warehouse_name': warehouse.name,
                        'available_quantity': item.available_quantity,
                        'reserved_quantity': item.reserved_quantity,
                        'threshold': self.low_stock_threshold
                    })

        return low_stock_products

    def cleanup_expired_reservations(self) -> int:
        """
        Background task to clean up expired reservations

        Returns number of reservations cleaned up
        """
        active_reservations = self.inventory_repo.find_active_reservations()
        expired_count = 0

        for reservation in active_reservations:
            if reservation.is_expired():
                try:
                    self.cancel_reservation(reservation.reservation_id)
                    expired_count += 1
                except Exception as e:
                    print(f"Failed to cleanup expired reservation {reservation.reservation_id}: {e}")

        if expired_count > 0:
            print(f"Cleaned up {expired_count} expired reservations")

        return expired_count

    def get_inventory_summary(self, product_id: str = None) -> Dict:
        """Get inventory summary for monitoring"""
        if product_id:
            inventory_items = self.inventory_repo.find_inventory_by_product(product_id)
        else:
            # Get all inventory (simplified for demo)
            warehouses = self.inventory_repo.find_active_warehouses()
            inventory_items = []
            for warehouse in warehouses:
                inventory_items.extend(
                    self.inventory_repo.find_inventory_by_warehouse(warehouse.warehouse_id)
                )

        total_available = sum(item.available_quantity for item in inventory_items)
        total_reserved = sum(item.reserved_quantity for item in inventory_items)

        return {
            'total_available': total_available,
            'total_reserved': total_reserved,
            'total_inventory': total_available + total_reserved,
            'warehouse_count': len(set(item.warehouse_id for item in inventory_items)),
            'low_stock_count': len([item for item in inventory_items
                                    if item.is_low_stock(self.low_stock_threshold)])
        }

    def _plan_inventory_allocation(self, cart_items: List[CartItem]) -> Optional[Dict[Tuple[str, str], int]]:
        """
        Plan how to allocate inventory across warehouses

        Returns: {(product_id, warehouse_id): quantity} or None if impossible

        Simple algorithm: prefer warehouses with most inventory
        Advanced: could consider shipping costs, location, etc.
        """
        allocation_plan = {}

        for cart_item in cart_items:
            remaining_needed = cart_item.quantity

            # Get all inventory items for this product, sorted by available quantity (descending)
            inventory_items = self.inventory_repo.find_inventory_by_product(cart_item.product_id)
            inventory_items.sort(key=lambda x: x.available_quantity, reverse=True)

            for inventory_item in inventory_items:
                if remaining_needed <= 0:
                    break

                can_allocate = min(remaining_needed, inventory_item.available_quantity)
                if can_allocate > 0:
                    key = (cart_item.product_id, inventory_item.warehouse_id)
                    allocation_plan[key] = can_allocate
                    remaining_needed -= can_allocate

            if remaining_needed > 0:
                # Cannot fulfill this item
                return None

        return allocation_plan

    def _rollback_reservations(self, reserved_items: List[Tuple[InventoryItem, int]]):
        """Rollback reservations in case of failure"""
        for inventory_item, quantity in reserved_items:
            try:
                inventory_item.release_reservation(quantity)
                self.inventory_repo.save_inventory_item(inventory_item)
            except Exception as e:
                print(f"Failed to rollback reservation: {e}")

    def _check_low_stock_alerts(self):
        """Send low stock alerts if configured"""
        if self.notification_service:
            low_stock_products = self.get_low_stock_products()
            if low_stock_products:
                self.notification_service.send_low_stock_alert(low_stock_products)

    def _start_background_cleanup(self):
        """Start background thread for cleanup tasks"""

        def cleanup_worker():
            while not self._stop_cleanup.wait(self.cleanup_interval_minutes * 60):
                try:
                    self.cleanup_expired_reservations()
                except Exception as e:
                    print(f"Background cleanup error: {e}")

        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        print("Started background inventory cleanup thread")

    def shutdown(self):
        """Shutdown service and cleanup resources"""
        self._stop_cleanup.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        print("Inventory service shutdown complete")