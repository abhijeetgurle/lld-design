import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from core.value_objects.money import Money


@dataclass
class CartItem:
    product_id: str
    quantity: int
    unit_price: Money

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

    def total_price(self) -> Money:
        return self.unit_price.multiply(self.quantity)

    def update_quantity(self, new_quantity: int):
        if new_quantity <= 0:
            raise ValueError("Quantity must be positive")
        self.quantity = new_quantity


@dataclass
class Cart:
    cart_id: str
    customer_id: str
    items: Dict[str, CartItem] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create_for_customer(cls, customer_id: str) -> 'Cart':
        return cls(
            cart_id=str(uuid.uuid4()),
            customer_id=customer_id
        )

    def add_item(self, product_id: str, quantity: int, unit_price: Money):
        """Add item to cart - core business logic"""
        if product_id in self.items:
            # Update existing item
            existing_item = self.items[product_id]
            existing_item.update_quantity(existing_item.quantity + quantity)
        else:
            # Add new item
            self.items[product_id] = CartItem(product_id, quantity, unit_price)

    def remove_item(self, product_id: str):
        """Remove item completely"""
        if product_id in self.items:
            del self.items[product_id]

    def update_item_quantity(self, product_id: str, new_quantity: int):
        """Update quantity of existing item"""
        if product_id not in self.items:
            raise ValueError(f"Product {product_id} not in cart")

        if new_quantity <= 0:
            self.remove_item(product_id)
        else:
            self.items[product_id].update_quantity(new_quantity)

    def clear(self):
        """Empty the cart"""
        self.items.clear()

    def is_empty(self) -> bool:
        """Check if cart has no items"""
        return len(self.items) == 0

    def total_items_count(self) -> int:
        """Total number of items (considering quantities)"""
        return sum(item.quantity for item in self.items.values())

    def total_amount(self) -> Money:
        """Calculate total price of all items"""
        if self.is_empty():
            return Money(0.0)

        # All items should have same currency (business rule)
        first_item = next(iter(self.items.values()))
        total = Money(0.0, first_item.unit_price.currency)
        for item in self.items.values():
            total = total.add(item.total_price())

        return total

    def get_items_list(self) -> List[CartItem]:
        """Get items as a list"""
        return list(self.items.values())