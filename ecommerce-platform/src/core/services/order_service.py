from typing import List

from core.entities.cart import Cart
from core.entities.order import Order, OrderStatus
from core.entities.user import Customer
from core.interfaces.repositories.order_repository import OrderRepository
from core.services.inventory_service import InventoryService
from core.services.payment_service import PaymentService


class OrderService:
    """
        Service that orchestrates order-related business workflows

        Key principles:
        1. Coordinates multiple entities
        2. Handles complex business workflows
        3. Manages transactions (all-or-nothing operations)
        4. Delegates to repositories for data access
        5. Uses other services for specific concerns
    """

    def __init__(self,
                 order_repository: OrderRepository,  # We'll define interfaces later
                 inventory_service: InventoryService,
                 payment_service: PaymentService,
                 notification_service: NotificationService):
        self.order_repo = order_repository
        self.inventory_service = inventory_service
        self.payment_service = payment_service
        self.notification_service = notification_service

    def place_order(self, cart: Cart, customer: Customer, payment_method: str):
        """
            Complex business workflow - this is what interviewers love to see!

            Workflow:
            1. Validate cart and customer
            2. Check inventory availability
            3. Reserve inventory
            4. Create order
            5. Process payment
            6. Confirm order or rollback
            7. Send notifications
        """
        # Step 1: Validation
        if cart.is_empty():
            raise ValueError("Cannot place order with empty cart")

        if not customer.is_active:
            raise ValueError("Customer account is deactivated")

        # Step 2: Check inventory availability
        if not self.inventory_service.check_availability(cart.get_items_list()):
            raise ValueError("Some items are out of stock")

        # Step 3: Reserve inventory (prevents overselling)
        reservation_id = self.inventory_service.reserve_items(cart.get_items_list())

        try:
            # Step 4: Create order (immutable snapshot)
            order = Order.create_from_cart(cart, customer.user_id)

            # Step 5: Process payment
            payment_result = self.payment_service.process_payment(
                amount=order.total_amount,
                method=payment_method,
                customer_id=customer.user_id
            )

            if not payment_result.is_successful():
                raise PaymentFailedException("Payment processing failed")

            # Step 6: Confirm order and inventory
            order.confirm()
            order.mark_paid()
            self.inventory_service.confirm_reservation(reservation_id)

            # Step 7: Save order
            saved_order = self.order_repo.save(order)

            # Step 8: Clear cart (order placed successfully)
            cart.clear()

            # Step 9: Send notifications
            self.notification_service.send_order_confirmation(saved_order, customer)

            return saved_order

        except Exception as e:
            # Rollback on any failure
            self.inventory_service.cancel_reservation(reservation_id)
            raise OrderCreationException(f"Failed to place order: {str(e)}")

    def cancel_order(self, order_id: int, customer_id: int) -> Order:
        order = self.order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        # Business rule: customers can only cancel their own orders
        if order.customer_id != customer_id:
            raise ValueError("Cannot cancel another customer's order")

        if not order.can_be_cancelled():
            raise ValueError("Order cannot be cancelled in current status")

        # Cancel order
        order.cancel()

        # Restore inventory
        self.inventory_service.restore_items(order.items)

        # Process refund if already paid
        if order.status == OrderStatus.PAID:
            self.payment_service.process_refund(order.order_id, order.total_amount)

        # Save and notify
        updated_order = self.order_repo.save(order)
        self.notification_service.send_cancellation_notice(updated_order)

        return updated_order

    def get_customer_orders(self, customer_id: int) -> List[Order]:
        return self.order_repo.find_by_customer_id(customer_id)

    def update_order_status(self, order_id: str, new_status: OrderStatus) -> Order:
        """Admin function to update order status"""
        order = self.order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        # Use the entity's business methods
        if new_status == OrderStatus.SHIPPED:
            order.ship()
        elif new_status == OrderStatus.DELIVERED:
            order.deliver()
        else:
            raise ValueError(f"Cannot update to status {new_status}")

        updated_order = self.order_repo.save(order)
        self.notification_service.send_status_update(updated_order)

        return updated_order


# Custom exceptions for better error handling
class OrderCreationException(Exception):
    pass

class PaymentFailedException(Exception):
    pass