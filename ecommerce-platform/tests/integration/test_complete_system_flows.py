#!/usr/bin/env python3
"""
Complete test script for all e-commerce flows

This script demonstrates:
1. User management flows
2. Product management flows
3. Cart operations flows
4. Order processing flows
5. Payment processing flows
6. Inventory management flows
7. Notification flows
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from datetime import datetime
from typing import List
import time

# Import your existing services
from core.entities.user import Customer, Seller, Admin
from core.entities.product import Product
from core.entities.cart import Cart
from core.entities.order import Order
from core.entities.payment import Payment, PaymentMethod
from core.value_objects.money import Money
from core.entities.notification import NotificationType, NotificationChannel, Priority
import uuid

# Import services
from core.services.notification_service import (
    NotificationService, EmailNotificationChannel, SMSNotificationChannel, SlackNotificationChannel
)
from core.repositories.in_memory_notification_repository import InMemoryNotificationRepository

# Mock classes for testing
class MockOrderService:
    def __init__(self, notification_service):
        self.notification_service = notification_service
    
    def place_order(self, cart: Cart, customer: Customer, payment_method: str) -> Order:
        """Simulate order placement with notifications"""
        # Create order from cart
        order = Order.create_from_cart(cart, customer.user_id)
        
        # Create and attach payment
        payment = Payment.create_for_order(
            order_id=order.order_id,
            customer_id=customer.user_id,
            amount=cart.total_amount(),
            method=PaymentMethod[payment_method]
        )
        order.attach_payment(payment)
        
        # Send order confirmation notification
        if self.notification_service:
            self.notification_service.send_order_confirmation(order, customer)
        
        return order

class MockPaymentService:
    def __init__(self, notification_service):
        self.notification_service = notification_service
    
    def process_payment(self, payment: Payment, customer_id: str) -> bool:
        """Simulate payment processing with notifications"""
        import random
        
        # Simulate payment success/failure
        success = random.choice([True, True, True, False])  # 75% success rate
        
        if success:
            payment.mark_successful(f"txn_{hash(str(payment))}")
            if self.notification_service:
                self.notification_service.send_payment_success(payment)
        else:
            payment.mark_failed("Insufficient funds")
            if self.notification_service:
                self.notification_service.send_payment_failure(payment, "Insufficient funds")
        
        return success


def setup_notification_service() -> NotificationService:
    """Setup notification service with all channels"""
    print("🔧 Setting up notification service...")
    
    notification_repo = InMemoryNotificationRepository()
    notification_service = NotificationService(notification_repo)
    
    # Register channels
    email_channel = EmailNotificationChannel({'from_email': 'noreply@ecommerce.com'})
    sms_channel = SMSNotificationChannel({'from_number': '+1234567890'})
    slack_channel = SlackNotificationChannel({'channel': '#ecommerce-alerts'})
    
    notification_service.register_channel(email_channel)
    notification_service.register_channel(sms_channel)
    notification_service.register_channel(slack_channel)
    
    print("✅ Notification service setup complete!")
    return notification_service


def test_1_user_management_flow():
    """Test 1: User management operations"""
    print("=" * 60)
    print("🧪 TEST 1: User Management Flow")
    print("=" * 60)
    
    # Create different types of users
    customer = Customer("customer_123", "john.doe@email.com", "John Doe")
    seller = Seller("seller_456", "seller@amazon.com", "Amazon Seller", "Amazon Inc")
    admin = Admin("admin_789", "admin@ecommerce.com", "System Admin")
    
    print(f"👤 Created Customer: {customer.name} ({customer.email})")
    print(f"🏪 Created Seller: {seller.name} ({seller.email})")
    print(f"👑 Created Admin: {admin.name} ({admin.email})")
    
    # Test permissions
    print(f"\n🔐 Permissions check:")
    print(f"   Customer can VIEW_PRODUCTS: {customer.can_perform('VIEW_PRODUCTS')}")
    print(f"   Seller can ADD_PRODUCT: {seller.can_perform('ADD_PRODUCT')}")
    print(f"   Admin can MANAGE_USERS: {admin.can_perform('MANAGE_USERS')}")
    
    # Test user operations
    print(f"\n👤 Testing user operations:")
    print(f"   Customer active: {customer.is_active}")
    customer.deactivate()
    print(f"   Customer deactivated: {not customer.is_active}")
    customer.is_active = True  # Reactivate for further tests
    
    # Test email update
    try:
        customer.update_email("john.doe.new@email.com")
        print(f"   Updated customer email: {customer.email}")
    except Exception as e:
        print(f"   Email update failed: {e}")
    
    print("✅ User management flow completed!\n")
    return {'customer': customer, 'seller': seller, 'admin': admin}


def test_2_product_management_flow(users):
    """Test 2: Product management operations"""
    print("=" * 60)
    print("🧪 TEST 2: Product Management Flow")
    print("=" * 60)
    
    seller = users['seller']
    
    # Create products
    products = []
    product_data = [
        ("iPhone 15 Pro", 999.99, "Electronics", "Latest iPhone with A17 Pro chip"),
        ("Samsung Galaxy S24", 899.99, "Electronics", "Flagship Android phone"),
        ("MacBook Air M3", 1199.99, "Computers", "Apple's latest laptop")
    ]
    
    for name, price, category, description in product_data:
        product = Product.create(
            name=name,
            price=Money(price),
            category=category,
            seller_id=seller.user_id
        )
        # Set description after creation since it's handled specially
        product.description = description
        products.append(product)
        print(f"📱 Created Product: {product.name} - ₹{product.price.amount}")
    
    # Test product operations
    product = products[0]
    original_price = product.price
    
    # Update price
    new_price = Money(1099.99)
    product.update_price(new_price)
    print(f"💰 Updated {product.name} price: ₹{original_price.amount} → ₹{product.price.amount}")
    
    # Test product validation
    print(f"🔍 Product validation:")
    print(f"   Product ID: {product.product_id}")
    print(f"   Category: {product.category}")
    print(f"   Created at: {product.created_at.strftime('%Y-%m-%d %H:%M')}")
    
    # Test invalid price update
    try:
        product.update_price(Money(-10.0))
        print(f"   ❌ Should not allow negative price")
    except ValueError as e:
        print(f"   ✅ Correctly prevented negative price: {e}")
    
    print("✅ Product management flow completed!\n")
    return products


def test_3_cart_operations_flow(users, products):
    """Test 3: Shopping cart operations"""
    print("=" * 60)
    print("🧪 TEST 3: Cart Operations Flow")
    print("=" * 60)
    
    customer = users['customer']
    
    # Create cart
    cart = Cart.create_for_customer(customer.user_id)
    print(f"🛒 Created cart for customer: {customer.name}")
    
    # Add items to cart
    cart.add_item(products[0].product_id, 1, products[0].price)  # iPhone
    cart.add_item(products[1].product_id, 2, products[1].price)  # Samsung (qty: 2)
    cart.add_item(products[2].product_id, 1, products[2].price)  # MacBook
    
    print(f"📦 Added {len(cart.items)} different products to cart")
    print(f"🧮 Total items in cart: {cart.total_items_count()}")
    print(f"💵 Cart total: ₹{cart.total_amount().amount}")

    # Test cart operations
    print(f"\n🛒 Cart contents:")
    for product_id, cart_item in cart.items.items():
        print(f"   - Product {product_id}: {cart_item.quantity} × ₹{cart_item.unit_price.amount}")

    # Update quantity
    cart.update_item_quantity(products[1].product_id, 3)
    print(f"\n🔄 Updated Samsung quantity to 3")
    print(f"💵 New cart total: ₹{cart.total_amount().amount}")

    # Remove item
    cart.remove_item(products[2].product_id)
    print(f"🗑️  Removed MacBook from cart")
    print(f"💵 Final cart total: ₹{cart.total_amount().amount}")
    
    print("✅ Cart operations flow completed!\n")
    return cart


def test_4_order_processing_flow(users, cart, notification_service):
    """Test 4: Order processing with notifications"""
    print("=" * 60)
    print("🧪 TEST 4: Order Processing Flow")
    print("=" * 60)
    
    customer = users['customer']
    
    # Create order service with notifications
    order_service = MockOrderService(notification_service)
    
    # Place order
    print(f"📝 Placing order for customer: {customer.name}")
    print(f"🛒 Cart total: ₹{cart.total_amount().amount}")
    
    order = order_service.place_order(cart, customer, "CREDIT_CARD")
    
    print(f"✅ Order placed successfully!")
    print(f"🆔 Order ID: {order.order_id}")
    print(f"📊 Order status: {order.status.name}")
    print(f"💳 Payment status: {order.payment.status}")
    
    # Test order state transitions
    print(f"\n🔄 Testing order state transitions...")
    
    try:
        order.confirm()
        print(f"✅ Order confirmed: {order.status.name}")
        
        order.mark_paid()
        print(f"💰 Order marked as paid")
        
        # Simulate shipping update
        tracking_id = "FEDEX123456789"
        notification_service.send_shipping_update(order, tracking_id)
        print(f"🚚 Shipping notification sent (Tracking: {tracking_id})")
        
    except Exception as e:
        print(f"❌ State transition error: {e}")
    
    # Wait for notifications to process
    time.sleep(2)
    
    print("✅ Order processing flow completed!\n")
    return order


def test_5_payment_processing_flow(users, cart, notification_service):
    """Test 5: Payment processing with notifications"""
    print("=" * 60)
    print("🧪 TEST 5: Payment Processing Flow")
    print("=" * 60)
    
    customer = users['customer']
    payment_service = MockPaymentService(notification_service)
    
    # Test multiple payment attempts
    payment_methods = ["CREDIT_CARD", "UPI", "WALLET"]
    
    for method in payment_methods:
        print(f"\n💳 Testing payment with {method}...")
        
        payment = Payment.create_for_order(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            customer_id=customer.user_id,
            amount=Money(100.0),  # Mock amount
            method=PaymentMethod[method]
        )
        success = payment_service.process_payment(payment, customer.user_id)
        
        if success:
            print(f"✅ Payment successful with {method}")
        else:
            print(f"❌ Payment failed with {method}")
    
    # Wait for notifications to process
    time.sleep(2)
    
    print("✅ Payment processing flow completed!\n")


def test_6_inventory_management_flow(notification_service):
    """Test 6: Inventory management with low stock alerts"""
    print("=" * 60)
    print("🧪 TEST 6: Inventory Management Flow")
    print("=" * 60)
    
    # Simulate low stock scenario
    low_stock_products = [
        {
            'product_id': 'prod_001',
            'warehouse_name': 'Mumbai Warehouse',
            'available_quantity': 3,
            'threshold': 10
        },
        {
            'product_id': 'prod_002',
            'warehouse_name': 'Delhi Warehouse', 
            'available_quantity': 1,
            'threshold': 10
        },
        {
            'product_id': 'prod_003',
            'warehouse_name': 'Bangalore Warehouse',
            'available_quantity': 5,
            'threshold': 10
        }
    ]
    
    print(f"⚠️  Simulating low stock scenario:")
    for product in low_stock_products:
        print(f"   - {product['product_id']}: {product['available_quantity']} remaining (threshold: {product['threshold']})")
    
    # Send low stock alert
    notifications = notification_service.send_low_stock_alert(low_stock_products)
    print(f"\n📨 Sent {len(notifications)} low stock alert notifications")
    
    # Wait for notifications to process
    time.sleep(2)
    
    print("✅ Inventory management flow completed!\n")


def test_7_notification_preferences_flow(users, notification_service):
    """Test 7: User notification preferences"""
    print("=" * 60)
    print("🧪 TEST 7: Notification Preferences Flow")
    print("=" * 60)
    
    customer = users['customer']
    
    # Set user preferences
    print(f"📋 Setting notification preferences for {customer.name}...")
    
    # Customer wants only email notifications for orders
    order_preference = notification_service.update_user_preferences(
        user_id=customer.user_id,
        notification_type=NotificationType.ORDER_CONFIRMATION,
        enabled_channels=[NotificationChannel.EMAIL],
        is_enabled=True
    )
    
    print(f"✅ Order notifications: {[ch.value for ch in order_preference.enabled_channels]}")
    
    # Customer disables payment notifications
    payment_preference = notification_service.update_user_preferences(
        user_id=customer.user_id,
        notification_type=NotificationType.PAYMENT_SUCCESS,
        enabled_channels=[],
        is_enabled=False
    )
    
    print(f"🔕 Payment notifications: disabled")
    
    # Test sending notifications with preferences
    print(f"\n📨 Testing notifications with preferences...")
    
    # This should send email notification
    mock_order = type('MockOrder', (), {
        'order_id': 'test_order_123',
        'customer_id': customer.user_id,
        'total_amount': Money(99.99),
        'items': ['item1', 'item2'],
        'created_at': datetime.now()
    })()
    
    order_notifications = notification_service.send_order_confirmation(mock_order, customer)
    print(f"📧 Order confirmation sent: {len(order_notifications)} notifications")
    
    # This should send no notifications (disabled)
    mock_payment = type('MockPayment', (), {
        'payment_id': 'test_payment_456',
        'customer_id': customer.user_id,
        'amount': Money(99.99),
        'method': type('PaymentMethod', (), {'value': 'CREDIT_CARD'})(),
        'transaction_id': 'txn_test_456',
        'processed_at': datetime.now()
    })()
    
    payment_notifications = notification_service.send_payment_success(mock_payment)
    print(f"💳 Payment success sent: {len(payment_notifications)} notifications (should be 0)")
    
    # Wait for notifications to process
    time.sleep(2)
    
    print("✅ Notification preferences flow completed!\n")


def test_8_notification_history_flow(users, notification_service):
    """Test 8: Notification history and tracking"""
    print("=" * 60)
    print("🧪 TEST 8: Notification History Flow")
    print("=" * 60)
    
    customer = users['customer']
    
    # Get notification history
    print(f"📚 Retrieving notification history for {customer.name}...")
    notifications = notification_service.get_user_notifications(customer.user_id, limit=10)
    
    print(f"📊 Found {len(notifications)} notifications in history")
    
    if notifications:
        print(f"\n📋 Recent notifications:")
        for i, notif in enumerate(notifications[:5], 1):
            status_emoji = "✅" if notif.status.value == "SENT" else "⏳" if notif.status.value == "PENDING" else "❌"
            print(f"   {i}. {status_emoji} {notif.notification_type.value} via {notif.channel.value}")
            print(f"      Subject: {notif.subject}")
            print(f"      Created: {notif.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if notif.sent_at:
                print(f"      Sent: {notif.sent_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
    
    # Get repository stats
    repo_stats = notification_service.notification_repo.get_stats()
    print(f"📈 Repository Statistics:")
    for key, value in repo_stats.items():
        print(f"   {key}: {value}")
    
    print("✅ Notification history flow completed!\n")


def test_9_end_to_end_customer_journey(notification_service):
    """Test 9: Complete end-to-end customer journey"""
    print("=" * 60)
    print("🧪 TEST 9: End-to-End Customer Journey")
    print("=" * 60)
    
    # Step 1: Customer registration
    customer = Customer("journey_customer", "alice@email.com", "Alice Johnson")
    print(f"👤 Step 1: Customer registered - {customer.name}")
    
    # Step 2: Browse and add products to cart
    cart = Cart.create_for_customer(customer.user_id)
    cart.add_item("prod_smartphone", 1, Money(599.99))
    cart.add_item("prod_case", 2, Money(29.99))
    print(f"🛒 Step 2: Added products to cart - Total: ₹{cart.total_amount().amount}")
    
    # Step 3: Checkout and place order
    order = Order.create_from_cart(cart, customer.user_id)
    payment = Payment.create_for_order(
        order_id=order.order_id,
        customer_id=customer.user_id,
        amount=cart.total_amount(),
        method=PaymentMethod.CREDIT_CARD
    )
    order.attach_payment(payment)
    order.confirm()
    print(f"📝 Step 3: Order placed and confirmed - {order.order_id}")
    
    # Send order confirmation
    notification_service.send_order_confirmation(order, customer)
    print(f"📧 Step 4: Order confirmation sent")
    
    # Step 4: Payment processing
    payment_service = MockPaymentService(notification_service)
    payment_success = payment_service.process_payment(order.payment, customer.user_id)
    
    if payment_success:
        order.mark_paid()
        print(f"💰 Step 5: Payment successful")
    else:
        print(f"❌ Step 5: Payment failed")
        return
    
    # Step 5: Order fulfillment and shipping
    tracking_id = "UPS987654321"
    notification_service.send_shipping_update(order, tracking_id)
    print(f"🚚 Step 6: Shipping notification sent - Tracking: {tracking_id}")
    
    # Wait for all notifications to process
    time.sleep(3)
    
    # Step 6: View notification history
    customer_notifications = notification_service.get_user_notifications(customer.user_id)
    print(f"📱 Step 7: Customer received {len(customer_notifications)} notifications")
    
    print("✅ End-to-end customer journey completed!\n")


def main():
    """Run all test flows"""
    print("🚀 Starting Complete E-commerce System Tests")
    print("=" * 80)
    
    # Setup notification service
    notification_service = setup_notification_service()
    
    try:
        # Run all test flows
        users = test_1_user_management_flow()
        products = test_2_product_management_flow(users)
        cart = test_3_cart_operations_flow(users, products)
        order = test_4_order_processing_flow(users, cart, notification_service)
        test_5_payment_processing_flow(users, cart, notification_service)
        test_6_inventory_management_flow(notification_service)
        test_7_notification_preferences_flow(users, notification_service)
        test_8_notification_history_flow(users, notification_service)
        test_9_end_to_end_customer_journey(notification_service)
        
        print("🎉 All system flow tests completed successfully!")
        print("=" * 80)
        
        # Final summary
        final_stats = notification_service.notification_repo.get_stats()
        service_stats = notification_service.get_service_stats()
        
        print("📊 FINAL SYSTEM SUMMARY:")
        print(f"   Total notifications processed: {final_stats['total_notifications']}")
        print(f"   Templates in system: {final_stats['total_templates']}")
        print(f"   User preferences set: {final_stats['total_preferences']}")
        print(f"   Channels registered: {service_stats['channels_registered']}")
        print(f"   Background processor active: {service_stats['background_thread_alive']}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print(f"\n🧹 Shutting down services...")
        notification_service.shutdown()
        print("✅ All tests completed and cleaned up!")


if __name__ == "__main__":
    main()
