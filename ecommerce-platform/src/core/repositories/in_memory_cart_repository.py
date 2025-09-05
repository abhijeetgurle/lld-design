from typing import Dict, Optional

from core.entities.cart import Cart
from core.interfaces.repositories.cart_repository import CartRepository


class InMemoryCartRepository(CartRepository):
    def __init__(self):
        self._carts: Dict[str, Cart] = {}
        self._customer_carts: Dict[str, str] = {}  # customer_id -> cart_id

    def save(self, cart: Cart) -> Cart:
        self._carts[cart.cart_id] = cart
        self._customer_carts[cart.customer_id] = cart.cart_id
        return cart

    def find_by_customer_id(self, customer_id: str) -> Optional[Cart]:
        cart_id = self._customer_carts.get(customer_id)
        if cart_id:
            return self._carts.get(cart_id)
        return None

    def delete(self, cart_id: str) -> bool:
        if cart_id in self._carts:
            cart = self._carts[cart_id]
            del self._carts[cart_id]
            del self._customer_carts[cart.customer_id]
            return True
        return False