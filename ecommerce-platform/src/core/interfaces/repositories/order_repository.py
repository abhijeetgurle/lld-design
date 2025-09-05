from abc import ABC, abstractmethod
from typing import Optional, List

from core.entities.order import Order, OrderStatus


class OrderRepository(ABC):
    """
       Abstract interface for order data access

       Key principles:
       1. Abstract interface (no implementation details)
       2. Domain-focused methods (not just CRUD)
       3. Returns domain entities
       4. Hides persistence technology
    """
    @abstractmethod
    def save(self, order: Order) -> Order:
        """Save order and return saved entity with any generated fields"""
        pass

    @abstractmethod
    def find_by_id(self, order_id: str) -> Optional[Order]:
        """Find order by ID"""
        pass

    @abstractmethod
    def find_by_customer_id(self, customer_id: str) -> List[Order]:
        """Find all orders for a customer"""
        pass

    @abstractmethod
    def find_by_status(self, status: OrderStatus) -> List[Order]:
        """Find orders by status (useful for processing workflows)"""
        pass

    @abstractmethod
    def find_pending_orders(self) -> List[Order]:
        """Business-specific query - find orders that need processing"""
        pass

    @abstractmethod
    def delete(self, order_id: str) -> bool:
        """Delete order (returns True if successful)"""
        pass