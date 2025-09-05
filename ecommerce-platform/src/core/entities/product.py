import uuid
from dataclasses import dataclass
from datetime import datetime

from core.value_objects.money import Money


@dataclass
class Product:
    product_id: str
    name: str
    description: str
    price: Money
    category: str
    seller_id: str
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self._validate()

    def _validate(self):
        if not self.name.strip():
            raise ValueError("Product name cannot be empty")
        if not self.price or self.price.amount <= 0:
            raise ValueError("Product price must be positive")
        if not self.category.strip():
            raise ValueError("Product category is required")

    @classmethod
    def create(cls, name: str, price: Money, category: str, seller_id: str, **kwargs) -> "Product":
        product_id = str(uuid.uuid4())
        return cls(
            product_id=product_id,
            name=name,
            description=kwargs.get('description', ''),
            price=price,
            category=category,
            seller_id=seller_id,
            **kwargs
        )

    def update_price(self, new_price: Money):
        """Business method for price updates"""
        if new_price.amount <= 0:
            raise ValueError("Price must be positive")
        self.price = new_price