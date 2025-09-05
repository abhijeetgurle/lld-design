from core.entities.order import Order
from core.entities.user import Customer, User
from core.repositories.in_memory_cart_repository import InMemoryCartRepository
from core.repositories.in_memory_order_repository import InMemoryOrderRepository
from core.repositories.in_memory_user_repository import InMemoryUserRepository
from core.services.cart_service import CartService
from core.services.order_service import OrderService


def create_ecommerce_system():
    """
        Composition Root - where we wire everything together

        This is where dependency injection happens:
        1. Create repositories
        2. Create services with dependencies
        3. Return configured system
    """
    # Repositories (data access layer)
    order_repo = InMemoryOrderRepository()
    user_repo = InMemoryUserRepository()
    cart_repo = InMemoryCartRepository()

    # External services (would be real implementations)
    inventory_service = MockInventoryService()
    payment_service = MockPaymentService()
    notification_service = MockNotificationService()

    # Application services (business logic layer)
    order_service = OrderService(
        order_repository=order_repo,
        inventory_service=inventory_service,
        payment_service=payment_service,
        notification_service=notification_service
    )

    cart_service = CartService(
        cart_repository=cart_repo,
        product_service=MockProductService()
    )

    # Return the configured system
    return EcommerceSystem(
        order_service=order_service,
        cart_service=cart_service,
        user_repository=user_repo
    )


class EcommerceSystem:
    """Main system facade"""

    def __init__(self, order_service, cart_service, user_repository):
        self.order_service = order_service
        self.cart_service = cart_service
        self.user_repo = user_repository

    def register_customer(self, email: str, name: str) -> Customer:
        customer = Customer(
            user_id=User.generate_id(),
            email=email,
            name=name
        )
        return self.user_repo.save(customer)

    def place_order(self, customer_id: str, payment_method: str) -> Order:
        # Get customer
        customer = self.user_repo.find_by_id(customer_id)
        if not customer:
            raise ValueError("Customer not found")

        # Get cart
        cart = self.cart_service.get_cart_for_customer(customer_id)
        if not cart:
            raise ValueError("No cart found")

        # Place order through service
        return self.order_service.place_order(cart, customer, payment_method)
