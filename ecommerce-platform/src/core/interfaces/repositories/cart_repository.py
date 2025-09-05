from abc import ABC, abstractmethod
from typing import Optional

from core.entities.cart import Cart


class CartRepository(ABC):
    @abstractmethod
    def save(self, cart: Cart) -> Cart:
        pass

    @abstractmethod
    def find_by_customer_id(self, customer_id: str) -> Optional[Cart]:
        pass

    @abstractmethod
    def delete(self, cart_id: str) -> bool:
        pass