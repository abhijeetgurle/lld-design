import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Dict, Optional


class ReservationStatus(Enum):
    ACTIVE = "ACTIVE"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


@dataclass
class InventoryItem:
    """
    Represents inventory for a specific product in a specific warehouse

    Key concepts:
    1. Available vs Reserved quantities
    2. Thread-safe operations
    3. Business rule enforcement
    """
    product_id: str
    warehouse_id: str
    available_quantity: int
    reserved_quantity: int = 0
    total_received: int = 0  # Audit trail
    total_sold: int = 0  # Audit trail
    last_updated: datetime = field(default_factory=datetime.now)

    # Thread safety for concurrent operations
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def __post_init__(self):
        if self.available_quantity < 0:
            raise ValueError("Available quantity cannot be negative")

    @property
    def total_quantity(self) -> int:
        """Total inventory (available + reserved)"""
        return self.available_quantity + self.reserved_quantity

    def can_reserve(self, quantity: int) -> bool:
        """Check if quantity can be reserved"""
        with self._lock:
            return self.available_quantity >= quantity

    def reserve(self, quantity: int) -> bool:
        """
        Reserve inventory (thread-safe)

        Business rules:
        1. Can only reserve from available quantity
        2. Atomic operation (all-or-nothing)
        3. Updates last_updated timestamp
        """
        if quantity <= 0:
            raise ValueError("Reservation quantity must be positive")

        with self._lock:
            if self.available_quantity >= quantity:
                self.available_quantity -= quantity
                self.reserved_quantity += quantity
                self.last_updated = datetime.now()
                return True
            return False

    def release_reservation(self, quantity: int) -> int:
        """
        Release reserved inventory back to available

        Returns actual quantity released (might be less than requested)
        """
        if quantity <= 0:
            raise ValueError("Release quantity must be positive")

        with self._lock:
            actual_release = min(quantity, self.reserved_quantity)
            self.reserved_quantity -= actual_release
            self.available_quantity += actual_release
            self.last_updated = datetime.now()
            return actual_release

    def confirm_reservation(self, quantity: int) -> int:
        """
        Confirm reservation (convert reserved to sold)

        This removes inventory permanently (sale completed)
        """
        if quantity <= 0:
            raise ValueError("Confirm quantity must be positive")

        with self._lock:
            actual_confirm = min(quantity, self.reserved_quantity)
            self.reserved_quantity -= actual_confirm
            self.total_sold += actual_confirm
            self.last_updated = datetime.now()
            return actual_confirm

    def add_stock(self, quantity: int) -> None:
        """Add new stock to inventory"""
        if quantity <= 0:
            raise ValueError("Stock addition must be positive")

        with self._lock:
            self.available_quantity += quantity
            self.total_received += quantity
            self.last_updated = datetime.now()

    def remove_stock(self, quantity: int, reason: str = "damaged") -> int:
        """
        Remove stock (e.g., damaged goods)

        Returns actual quantity removed
        """
        if quantity <= 0:
            raise ValueError("Stock removal must be positive")

        with self._lock:
            actual_removal = min(quantity, self.available_quantity)
            self.available_quantity -= actual_removal
            self.last_updated = datetime.now()
            return actual_removal

    def is_low_stock(self, threshold: int = 10) -> bool:
        """Check if inventory is below threshold"""
        return self.total_quantity <= threshold


@dataclass
class InventoryReservation:
    """
    Tracks a temporary inventory reservation
    Prevents overselling during checkout process
    """
    reservation_id: str
    customer_id: str
    items: Dict[str, int]  # "{product_id}_{warehouse_id}" -> quantity
    status: ReservationStatus = ReservationStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = None
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    def __post_init__(self):
        if self.expires_at is None:
            # Default 15-minute expiry
            self.expires_at = self.created_at + timedelta(minutes=15)

    @classmethod
    def create(cls, customer_id: str, items: Dict[str, int], expiry_minutes: int = 15) -> 'InventoryReservation':
        """Factory method for creating reservations"""
        return cls(
            reservation_id=str(uuid.uuid4()),
            customer_id=customer_id,
            items=items.copy(),
            expires_at=datetime.now() + timedelta(minutes=expiry_minutes)
        )

    def is_expired(self) -> bool:
        """Check if reservation has expired"""
        return (datetime.now() > self.expires_at and
                self.status == ReservationStatus.ACTIVE)

    def is_active(self) -> bool:
        """Check if reservation is active and not expired"""
        return (self.status == ReservationStatus.ACTIVE and
                not self.is_expired())

    def confirm(self) -> None:
        """Confirm the reservation (inventory sold)"""
        if not self.is_active():
            raise ValueError("Cannot confirm inactive or expired reservation")

        self.status = ReservationStatus.CONFIRMED
        self.confirmed_at = datetime.now()

    def cancel(self) -> None:
        """Cancel the reservation (return inventory)"""
        if self.status in [ReservationStatus.CONFIRMED, ReservationStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel {self.status} reservation")

        self.status = ReservationStatus.CANCELLED
        self.cancelled_at = datetime.now()

    def extend_expiry(self, additional_minutes: int) -> None:
        """Extend reservation expiry time"""
        if not self.is_active():
            raise ValueError("Cannot extend inactive reservation")

        self.expires_at += timedelta(minutes=additional_minutes)


@dataclass
class Warehouse:
    """
    Warehouse entity with location and capacity management
    """
    warehouse_id: str
    name: str
    location: str
    is_active: bool = True
    max_capacity: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)

    def can_accept_inventory(self, quantity: int = 1) -> bool:
        """Check if warehouse can accept more inventory"""
        if not self.is_active:
            return False

        if self.max_capacity is None:
            return True

        # In real implementation, would check current total inventory
        return True  # Simplified for demo