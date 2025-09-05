from typing import Dict, Optional, List

from core.entities.order import Order, OrderStatus
from core.interfaces.repositories.order_repository import OrderRepository


class InMemoryOrderRepository(OrderRepository):
    """
        In-memory implementation of OrderRepository

        Perfect for:
        1. LLD interviews (no database complexity)
        2. Unit testing
        3. Prototyping
        4. Demonstrating the pattern
    """
    def __init__(self):
        self._orders: Dict[str, Order] = {}
        self._next_id = 1

    def save(self, order: Order) -> Order:
        """Save order in memory"""
        # In real implementation, this might generate ID, update timestamps, etc.
        self._orders[order.order_id] = order
        return order

    def find_by_id(self, order_id: str) -> Optional[Order]:
        """Find by ID with None handling"""
        return self._orders.get(order_id)

    def find_by_customer_id(self, customer_id: str) -> List[Order]:
        """Filter orders by customer"""
        return [
            order for order in self._orders.values()
            if order.customer_id == customer_id
        ]

    def find_by_status(self, status: OrderStatus) -> List[Order]:
        """Find orders by status"""
        return [
            order for order in self._orders.values()
            if order.status == status
        ]

    def find_pending_orders(self) -> List[Order]:
        """Business query - implemented in terms of other methods"""
        return self.find_by_status(OrderStatus.PENDING)

    def delete(self, order_id: str) -> bool:
        """Delete order"""
        if order_id in self._orders:
            del self._orders[order_id]
            return True
        return False

    # Additional methods for testing/debugging
    def count(self) -> int:
        """Get total number of orders"""
        return len(self._orders)

    def clear(self):
        """Clear all orders (useful for testing)"""
        self._orders.clear()