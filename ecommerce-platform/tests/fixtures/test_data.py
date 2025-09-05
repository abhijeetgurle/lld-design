#!/usr/bin/env python3
"""
Test fixtures and data builders for e-commerce system tests

Provides reusable test data and builder patterns for creating test objects
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from datetime import datetime
from typing import List, Dict, Any
import uuid

from core.entities.user import Customer, Seller, Admin
from core.entities.product import Product
from core.entities.cart import Cart, CartItem
from core.entities.order import Order, OrderItem
from core.entities.payment import Payment, PaymentMethod
from core.entities.notification import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationType, NotificationChannel, Priority
)
from core.value_objects.money import Money


class UserBuilder:
    """Builder pattern for creating test users"""
    
    def __init__(self):
        self.user_id = f"user_{uuid.uuid4().hex[:8]}"
        self.email = "test@example.com"
        self.name = "Test User"
        self.is_active = True
    
    def with_id(self, user_id: str):
        self.user_id = user_id
        return self
    
    def with_email(self, email: str):
        self.email = email
        return self
    
    def with_name(self, name: str):
        self.name = name
        return self
    
    def inactive(self):
        self.is_active = False
        return self
    
    def build_customer(self, shipping_addresses: List[str] = None) -> Customer:
        customer = Customer(self.user_id, self.email, self.name, shipping_addresses)
        customer.is_active = self.is_active
        return customer
    
    def build_seller(self, business_name: str = "Test Business") -> Seller:
        seller = Seller(self.user_id, self.email, self.name, business_name)
        seller.is_active = self.is_active
        return seller
    
    def build_admin(self) -> Admin:
        admin = Admin(self.user_id, self.email, self.name)
        admin.is_active = self.is_active
        return admin


class ProductBuilder:
    """Builder pattern for creating test products"""
    
    def __init__(self):
        self.product_id = f"prod_{uuid.uuid4().hex[:8]}"
        self.name = "Test Product"
        self.price = Money(99.99)
        self.category = "Electronics"
        self.seller_id = f"seller_{uuid.uuid4().hex[:8]}"
        self.description = "Test product description"
    
    def with_id(self, product_id: str):
        self.product_id = product_id
        return self
    
    def with_name(self, name: str):
        self.name = name
        return self
    
    def with_price(self, amount: float, currency: str = "INR"):
        self.price = Money(amount, currency)
        return self
    
    def with_category(self, category: str):
        self.category = category
        return self
    
    def with_seller(self, seller_id: str):
        self.seller_id = seller_id
        return self
    
    def with_description(self, description: str):
        self.description = description
        return self
    
    def build(self) -> Product:
        product = Product(
            product_id=self.product_id,
            name=self.name,
            description=self.description,
            price=self.price,
            category=self.category,
            seller_id=self.seller_id
        )
        return product


class CartBuilder:
    """Builder pattern for creating test carts"""
    
    def __init__(self):
        self.cart_id = f"cart_{uuid.uuid4().hex[:8]}"
        self.customer_id = f"customer_{uuid.uuid4().hex[:8]}"
        self.items = []
    
    def for_customer(self, customer_id: str):
        self.customer_id = customer_id
        return self
    
    def with_item(self, product_id: str, quantity: int, unit_price: Money):
        self.items.append((product_id, quantity, unit_price))
        return self
    
    def with_product(self, product: Product, quantity: int = 1):
        self.items.append((product.product_id, quantity, product.price))
        return self
    
    def build(self) -> Cart:
        cart = Cart(self.cart_id, self.customer_id)
        for product_id, quantity, unit_price in self.items:
            cart.add_item(product_id, quantity, unit_price)
        return cart


class OrderBuilder:
    """Builder pattern for creating test orders"""
    
    def __init__(self):
        self.order_id = f"order_{uuid.uuid4().hex[:8]}"
        self.customer_id = f"customer_{uuid.uuid4().hex[:8]}"
        self.items = []
        self.payment = None
    
    def with_id(self, order_id: str):
        self.order_id = order_id
        return self
    
    def for_customer(self, customer_id: str):
        self.customer_id = customer_id
        return self
    
    def with_item(self, product_id: str, product_name: str, quantity: int, unit_price: Money):
        order_item = OrderItem(product_id, product_name, quantity, unit_price)
        self.items.append(order_item)
        return self
    
    def with_payment(self, payment: Payment):
        self.payment = payment
        return self
    
    def from_cart(self, cart: Cart, customer_id: str = None):
        if customer_id:
            self.customer_id = customer_id
        else:
            self.customer_id = cart.customer_id
        
        for cart_item in cart.get_items_list():
            self.with_item(
                cart_item.product_id,
                f"Product-{cart_item.product_id}",
                cart_item.quantity,
                cart_item.unit_price
            )
        return self
    
    def build(self) -> Order:
        if not self.items:
            # Add a default item if none provided
            self.with_item("default_product", "Default Product", 1, Money(50.0))
        
        order = Order(self.order_id, self.customer_id, self.items, self.payment)
        return order


class PaymentBuilder:
    """Builder pattern for creating test payments"""
    
    def __init__(self):
        self.payment_id = f"pay_{uuid.uuid4().hex[:8]}"
        self.order_id = f"order_{uuid.uuid4().hex[:8]}"
        self.customer_id = f"customer_{uuid.uuid4().hex[:8]}"
        self.amount = Money(100.0)
        self.method = PaymentMethod.CREDIT_CARD
    
    def with_id(self, payment_id: str):
        self.payment_id = payment_id
        return self
    
    def for_order(self, order_id: str):
        self.order_id = order_id
        return self
    
    def for_customer(self, customer_id: str):
        self.customer_id = customer_id
        return self
    
    def with_amount(self, amount: float, currency: str = "INR"):
        self.amount = Money(amount, currency)
        return self
    
    def with_method(self, method: PaymentMethod):
        self.method = method
        return self
    
    def build(self) -> Payment:
        return Payment(
            payment_id=self.payment_id,
            order_id=self.order_id,
            customer_id=self.customer_id,
            amount=self.amount,
            method=self.method
        )


class NotificationBuilder:
    """Builder pattern for creating test notifications"""
    
    def __init__(self):
        self.notification_id = f"notif_{uuid.uuid4().hex[:8]}"
        self.user_id = f"user_{uuid.uuid4().hex[:8]}"
        self.notification_type = NotificationType.ORDER_CONFIRMATION
        self.channel = NotificationChannel.EMAIL
        self.subject = "Test Notification"
        self.body = "This is a test notification"
        self.recipient = "test@example.com"
        self.priority = Priority.MEDIUM
    
    def with_id(self, notification_id: str):
        self.notification_id = notification_id
        return self
    
    def for_user(self, user_id: str):
        self.user_id = user_id
        return self
    
    def with_type(self, notification_type: NotificationType):
        self.notification_type = notification_type
        return self
    
    def with_channel(self, channel: NotificationChannel):
        self.channel = channel
        return self
    
    def with_content(self, subject: str, body: str):
        self.subject = subject
        self.body = body
        return self
    
    def with_recipient(self, recipient: str):
        self.recipient = recipient
        return self
    
    def with_priority(self, priority: Priority):
        self.priority = priority
        return self
    
    def build(self) -> Notification:
        return Notification(
            notification_id=self.notification_id,
            user_id=self.user_id,
            notification_type=self.notification_type,
            channel=self.channel,
            subject=self.subject,
            body=self.body,
            recipient=self.recipient,
            priority=self.priority
        )


# Predefined test data
class TestData:
    """Commonly used test data"""
    
    @staticmethod
    def sample_customer() -> Customer:
        return UserBuilder().with_email("john.doe@example.com").with_name("John Doe").build_customer()
    
    @staticmethod
    def sample_seller() -> Seller:
        return UserBuilder().with_email("seller@amazon.com").with_name("Amazon Seller").build_seller("Amazon Inc")
    
    @staticmethod
    def sample_admin() -> Admin:
        return UserBuilder().with_email("admin@ecommerce.com").with_name("System Admin").build_admin()
    
    @staticmethod
    def sample_products() -> List[Product]:
        seller_id = "seller_123"
        return [
            ProductBuilder().with_name("iPhone 15 Pro").with_price(99999.99).with_seller(seller_id).build(),
            ProductBuilder().with_name("Samsung Galaxy S24").with_price(79999.99).with_seller(seller_id).build(),
            ProductBuilder().with_name("MacBook Air M3").with_price(119999.99).with_category("Computers").with_seller(seller_id).build()
        ]
    
    @staticmethod
    def sample_cart_with_items(customer_id: str = None) -> Cart:
        if not customer_id:
            customer_id = "customer_123"
        
        products = TestData.sample_products()
        return (CartBuilder()
                .for_customer(customer_id)
                .with_product(products[0], 1)
                .with_product(products[1], 2)
                .build())
    
    @staticmethod
    def sample_order(customer_id: str = None) -> Order:
        if not customer_id:
            customer_id = "customer_123"
        
        cart = TestData.sample_cart_with_items(customer_id)
        return OrderBuilder().from_cart(cart).build()
    
    @staticmethod
    def sample_payment(order_id: str = None, customer_id: str = None) -> Payment:
        return (PaymentBuilder()
                .for_order(order_id or "order_123")
                .for_customer(customer_id or "customer_123")
                .with_amount(1000.0)
                .with_method(PaymentMethod.UPI)
                .build())
    
    @staticmethod
    def sample_notification_template() -> NotificationTemplate:
        return NotificationTemplate(
            template_id="test_order_confirmation",
            notification_type=NotificationType.ORDER_CONFIRMATION,
            channel=NotificationChannel.EMAIL,
            subject_template="Order #{order_id} Confirmed",
            body_template="Dear {customer_name}, your order #{order_id} for {amount} has been confirmed.",
            variables=['order_id', 'customer_name', 'amount']
        )
    
    @staticmethod
    def sample_notification_preference(user_id: str = None) -> NotificationPreference:
        return NotificationPreference(
            user_id=user_id or "user_123",
            notification_type=NotificationType.ORDER_CONFIRMATION,
            enabled_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
            is_enabled=True
        )


# Scenarios for testing complex workflows
class TestScenarios:
    """Complex test scenarios combining multiple entities"""
    
    @staticmethod
    def complete_order_flow():
        """Create a complete order flow scenario"""
        customer = TestData.sample_customer()
        seller = TestData.sample_seller()
        products = TestData.sample_products()
        
        # Update products to use the seller's ID
        for product in products:
            product.seller_id = seller.user_id
        
        cart = CartBuilder().for_customer(customer.user_id).build()
        for product in products[:2]:  # Add first 2 products
            cart.add_item(product.product_id, 1, product.price)
        
        order = Order.create_from_cart(cart, customer.user_id)
        payment = Payment.create_for_order(
            order.order_id, 
            customer.user_id, 
            order.total_amount, 
            PaymentMethod.CREDIT_CARD
        )
        order.attach_payment(payment)
        
        return {
            'customer': customer,
            'seller': seller,
            'products': products,
            'cart': cart,
            'order': order,
            'payment': payment
        }
    
    @staticmethod
    def failed_payment_scenario():
        """Create a scenario with failed payment"""
        scenario = TestScenarios.complete_order_flow()
        payment = scenario['payment']
        payment.mark_failed("Insufficient funds")
        
        return scenario
    
    @staticmethod
    def notification_preferences_scenario():
        """Create scenario with various notification preferences"""
        customer = TestData.sample_customer()
        
        preferences = [
            NotificationPreference(
                user_id=customer.user_id,
                notification_type=NotificationType.ORDER_CONFIRMATION,
                enabled_channels=[NotificationChannel.EMAIL],
                is_enabled=True
            ),
            NotificationPreference(
                user_id=customer.user_id,
                notification_type=NotificationType.PAYMENT_SUCCESS,
                enabled_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
                is_enabled=True
            ),
            NotificationPreference(
                user_id=customer.user_id,
                notification_type=NotificationType.PROMOTIONAL,
                enabled_channels=[],
                is_enabled=False  # Disabled
            )
        ]
        
        return {
            'customer': customer,
            'preferences': preferences
        }
