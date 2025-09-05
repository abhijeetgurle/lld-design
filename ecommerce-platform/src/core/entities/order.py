import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from core.entities.cart import Cart
from core.entities.payment import Payment
from core.value_objects.money import Money


class OrderStatus(Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


@dataclass
class OrderItem:
    """Order item - snapshot of product at time of order"""
    product_id: str
    product_name: str  # Snapshot - product name might change later
    quantity: int
    unit_price: Money

    def total_price(self) -> Money:
        return self.unit_price.multiply(self.quantity)


@dataclass
class Order:
    order_id: str
    customer_id: str
    items: List[OrderItem]
    payment: Optional[Payment] = None
    status: OrderStatus = OrderStatus.PENDING
    total_amount: Money = None
    created_at: datetime = field(default_factory=datetime.now)
    confirmed_at: datetime = None
    shipped_at: datetime = None
    delivered_at: datetime = None

    def __post_init__(self):
        if not self.items:
            raise ValueError("Order must have at least one item")

        if self.total_amount is None:
            self.total_amount = self._calculate_total()

    @classmethod
    def create_from_cart(cls, cart: Cart, customer_id: str) -> 'Order':
        """Factory method - create order from cart"""
        if cart.is_empty():
            raise ValueError("Cannot create order from empty cart")

        order_items = []
        for cart_item in cart.get_items_list():
            # Create immutable snapshot of cart item
            order_item = OrderItem(
                product_id=cart_item.product_id,
                product_name=f"Product-{cart_item.product_id}",  # Would get from product services
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price
            )
            order_items.append(order_item)

        return cls(
            order_id=str(uuid.uuid4()),
            customer_id=customer_id,
            items=order_items
        )

    def confirm(self):
        """Business method - confirm the order"""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot confirm order in {self.status} status")

        self.status = OrderStatus.CONFIRMED
        self.confirmed_at = datetime.now()

    def mark_paid(self):
        """Business method - mark as paid"""
        if self.status != OrderStatus.CONFIRMED:
            raise ValueError(f"Cannot mark paid order in {self.status} status")

        self.status = OrderStatus.PAID

    def ship(self):
        """Business method - ship the order"""
        if self.status != OrderStatus.PAID:
            raise ValueError(f"Cannot ship order in {self.status} status")

        self.status = OrderStatus.SHIPPED
        self.shipped_at = datetime.now()

    def deliver(self):
        """Business method - mark as delivered"""
        if self.status != OrderStatus.SHIPPED:
            raise ValueError(f"Cannot deliver order in {self.status} status")

        self.status = OrderStatus.DELIVERED
        self.delivered_at = datetime.now()

    def cancel(self):
        """Business method - cancel order (with business rules)"""
        if self.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise ValueError("Cannot cancel shipped or delivered order")

        self.status = OrderStatus.CANCELLED

    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled"""
        return self.status not in [OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.CANCELLED]

    def get_total_items_count(self) -> int:
        """Total number of items in order"""
        return sum(item.quantity for item in self.items)

    def _calculate_total(self) -> Money:
        """Private method to calculate total amount"""
        if not self.items:
            return Money(0.0)

        first_item = self.items[0]
        total = Money(0.0, first_item.unit_price.currency)

        for item in self.items:
            total = total.add(item.total_price())

        return total

    def attach_payment(self, payment: Payment) -> None:
        """Business method to attach payment to order"""
        if payment.order_id != self.order_id:
            raise ValueError("Payment order_id must match order")

        if payment.amount != self.total_amount:
            raise ValueError("Payment amount must match order total")

        self.payment = payment

    def is_paid(self) -> bool:
        """Business query - check if order is paid"""
        return self.payment and self.payment.is_successful()

    def can_be_shipped(self) -> bool:
        """Business rule - orders can only be shipped if paid"""
        return self.is_paid() and self.status == OrderStatus.CONFIRMED