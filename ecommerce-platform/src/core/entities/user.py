import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class User(ABC):
    user_id: str
    email: str
    name: str
    created_at: datetime = None
    is_active: bool = True

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

        self._validate()

    def _validate(self):
        if not self.email or "@" not in self.email:
            raise ValueError("Valid email required")
        if not self.name or not self.name.strip():
            raise ValueError("Name cannot be empty")

    @classmethod
    def generate_id(cls) -> str:
        """Factory method for generating unique IDs"""
        return str(uuid.uuid4())

    def deactivate(self):
        self.is_active = False

    def update_email(self, new_email):
        old_email = self.email
        self.email = new_email
        try:
            self._validate()
        except ValueError:
            self.email = old_email  # Rollback on validation failure
            raise

    @abstractmethod
    def get_permissions(self) -> str:
        pass

    def can_perform(self, permission: str) -> bool:
        return permission in self.get_permissions()


@dataclass
class Customer(User):
    shipping_addresses: List[str] = None

    def __post_init__(self):
        super().__post_init__()
        if self.shipping_addresses is None:
            self.shipping_addresses = []

    def get_permissions(self) -> List[str]:
        return ["VIEW_PRODUCTS", "ADD_TO_CART", "PLACE_ORDER", "VIEW_ORDERS"]


@dataclass
class Seller(User):
    business_name: str = ""

    def get_permissions(self) -> List[str]:
        return ["ADD_PRODUCT", "UPDATE_PRODUCT", "VIEW_SALES", "MANAGE_INVENTORY"]


@dataclass
class Admin(User):
    def get_permissions(self) -> List[str]:
        return [
            "MANAGE_USERS", "MANAGE_PRODUCTS", "MANAGE_ORDERS",
            "VIEW_ANALYTICS", "MANAGE_SYSTEM", "MANAGE_WAREHOUSES"
        ]