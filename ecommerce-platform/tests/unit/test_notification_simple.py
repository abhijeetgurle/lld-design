#!/usr/bin/env python3
"""
Simplified unit tests for notification components

Tests core functionality without complex background processing
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from core.repositories.in_memory_notification_repository import InMemoryNotificationRepository
from core.entities.notification import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationType, NotificationChannel, NotificationStatus, Priority
)

def test_notification_repository():
    """Test notification repository functionality"""
    print("🧪 Testing NotificationRepository...")
    
    repo = InMemoryNotificationRepository()
    
    # Test saving and retrieving a notification
    notification = Notification.create(
        user_id="user_123",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        channel=NotificationChannel.EMAIL,
        subject="Test Subject",
        body="Test Body",
        recipient="test@example.com"
    )
    
    saved = repo.save_notification(notification)
    retrieved = repo.find_notification(notification.notification_id)
    
    assert saved.notification_id == notification.notification_id
    assert retrieved is not None
    assert retrieved.subject == "Test Subject"
    print("   ✅ Notification save/retrieve successful")
    
    # Test user notifications
    user_notifications = repo.find_user_notifications("user_123")
    assert len(user_notifications) == 1
    assert user_notifications[0].user_id == "user_123"
    print("   ✅ User notifications query successful")
    
    # Test template management
    template = NotificationTemplate(
        template_id="test_template",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        channel=NotificationChannel.EMAIL,
        subject_template="Order #{order_id} Confirmed",
        body_template="Dear {customer_name}, order #{order_id} confirmed.",
        variables=['order_id', 'customer_name']
    )
    
    saved_template = repo.save_template(template)
    retrieved_template = repo.find_template(
        NotificationType.ORDER_CONFIRMATION,
        NotificationChannel.EMAIL
    )
    
    assert saved_template.template_id == "test_template"
    assert retrieved_template is not None
    assert retrieved_template.subject_template == "Order #{order_id} Confirmed"
    print("   ✅ Template save/retrieve successful")
    
    # Test preferences
    preference = NotificationPreference(
        user_id="user_123",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        enabled_channels=[NotificationChannel.EMAIL],
        is_enabled=True
    )
    
    saved_pref = repo.save_preference(preference)
    retrieved_pref = repo.find_user_preference(
        "user_123", 
        NotificationType.ORDER_CONFIRMATION
    )
    
    assert saved_pref.user_id == "user_123"
    assert retrieved_pref is not None
    assert retrieved_pref.is_enabled == True
    assert NotificationChannel.EMAIL in retrieved_pref.enabled_channels
    print("   ✅ Preference save/retrieve successful")
    
    # Test repository statistics
    stats = repo.get_stats()
    assert stats['total_notifications'] >= 1
    assert stats['total_templates'] >= 1
    assert stats['total_preferences'] >= 1
    print("   ✅ Repository statistics successful")


def test_notification_template_rendering():
    """Test notification template rendering"""
    print("🧪 Testing Template Rendering...")
    
    repo = InMemoryNotificationRepository()
    
    # Create a template with variables
    template = NotificationTemplate(
        template_id="order_template",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        channel=NotificationChannel.EMAIL,
        subject_template="Your order #{order_id} is ready!",
        body_template="Hello {customer_name}, your order #{order_id} for {amount} has been confirmed on {date}.",
        variables=['order_id', 'customer_name', 'amount', 'date']
    )
    
    repo.save_template(template)
    
    # Test successful rendering
    variables = {
        'order_id': 'ORD-12345',
        'customer_name': 'John Doe',
        'amount': '$99.99',
        'date': '2024-01-15'
    }
    
    subject = template.render_subject(variables)
    body = template.render_body(variables)
    
    assert subject == "Your order #ORD-12345 is ready!"
    assert "John Doe" in body
    assert "ORD-12345" in body
    assert "$99.99" in body
    assert "2024-01-15" in body
    print("   ✅ Template rendering successful")
    
    # Test validation
    incomplete_vars = {'order_id': 'ORD-123'}
    missing = template.validate_variables(incomplete_vars)
    
    assert len(missing) == 3  # customer_name, amount, date are missing
    assert 'customer_name' in missing
    assert 'amount' in missing
    assert 'date' in missing
    print("   ✅ Template validation successful")
    
    # Test rendering with missing variables (should fail)
    try:
        template.render_body(incomplete_vars)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Missing template variable" in str(e)
        print("   ✅ Missing variable error handling successful")


def test_notification_preferences_logic():
    """Test notification preference business logic"""
    print("🧪 Testing Preference Logic...")
    
    # Test enabled preference
    enabled_pref = NotificationPreference(
        user_id="user_123",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        enabled_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
        is_enabled=True
    )
    
    assert enabled_pref.is_channel_enabled(NotificationChannel.EMAIL) == True
    assert enabled_pref.is_channel_enabled(NotificationChannel.SMS) == True
    assert enabled_pref.is_channel_enabled(NotificationChannel.SLACK) == False
    print("   ✅ Enabled preference logic successful")
    
    # Test disabled preference (should block all channels)
    disabled_pref = NotificationPreference(
        user_id="user_123",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        enabled_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
        is_enabled=False  # Disabled overrides enabled_channels
    )
    
    assert disabled_pref.is_channel_enabled(NotificationChannel.EMAIL) == False
    assert disabled_pref.is_channel_enabled(NotificationChannel.SMS) == False
    print("   ✅ Disabled preference logic successful")
    
    # Test quiet hours
    from datetime import datetime
    quiet_pref = NotificationPreference(
        user_id="user_123",
        notification_type=NotificationType.PROMOTIONAL,
        enabled_channels=[NotificationChannel.EMAIL],
        is_enabled=True,
        quiet_hours_start="22:00",
        quiet_hours_end="08:00"
    )
    
    # Test during quiet hours
    quiet_time = datetime.now().replace(hour=23, minute=30)
    assert quiet_pref.is_in_quiet_hours(quiet_time) == True
    
    # Test outside quiet hours
    active_time = datetime.now().replace(hour=14, minute=30)
    assert quiet_pref.is_in_quiet_hours(active_time) == False
    print("   ✅ Quiet hours logic successful")


def test_notification_lifecycle():
    """Test notification state transitions"""
    print("🧪 Testing Notification Lifecycle...")
    
    # Create a notification
    notification = Notification.create(
        user_id="user_123",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        channel=NotificationChannel.EMAIL,
        subject="Order Confirmed",
        body="Your order has been confirmed",
        recipient="test@example.com",
        priority=Priority.HIGH
    )
    
    # Initially pending
    assert notification.status == NotificationStatus.PENDING
    assert notification.retry_count == 0
    assert notification.sent_at is None
    assert notification.failed_at is None
    print("   ✅ Initial state correct")
    
    # Mark as sent
    response_data = {"message_id": "msg_123", "provider": "email_service"}
    notification.mark_sent(response_data)
    
    assert notification.status == NotificationStatus.SENT
    assert notification.sent_at is not None
    assert notification.provider_response == response_data
    print("   ✅ Mark sent successful")
    
    # Test failure flow with new notification
    failed_notification = Notification.create(
        user_id="user_456",
        notification_type=NotificationType.PAYMENT_SUCCESS,
        channel=NotificationChannel.SMS,
        subject="Payment Confirmed",
        body="Payment successful",
        recipient="+1234567890"
    )
    
    # Mark as failed
    error_msg = "SMS service unavailable"
    failed_notification.mark_failed(error_msg)
    
    assert failed_notification.status == NotificationStatus.FAILED
    assert failed_notification.failed_at is not None
    assert failed_notification.error_message == error_msg
    assert failed_notification.retry_count == 1
    print("   ✅ Mark failed successful")
    
    # Test retry logic
    assert failed_notification.can_retry() == True
    
    # Reset for retry
    failed_notification.reset_for_retry()
    assert failed_notification.status == NotificationStatus.RETRY
    assert failed_notification.error_message is None
    assert failed_notification.provider_response is None
    print("   ✅ Retry logic successful")
    
    # Test max retries exceeded
    failed_notification.retry_count = failed_notification.max_retries
    assert failed_notification.can_retry() == False
    print("   ✅ Max retries logic successful")


def test_notification_priority_and_filtering():
    """Test notification priority and filtering"""
    print("🧪 Testing Priority and Filtering...")
    
    repo = InMemoryNotificationRepository()
    
    # Create notifications with different priorities
    high_priority = Notification.create(
        user_id="user_123",
        notification_type=NotificationType.PAYMENT_FAILED,
        channel=NotificationChannel.EMAIL,
        subject="Payment Failed",
        body="Payment failed",
        recipient="test@example.com",
        priority=Priority.HIGH
    )
    
    medium_priority = Notification.create(
        user_id="user_123",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        channel=NotificationChannel.EMAIL,
        subject="Order Confirmed",
        body="Order confirmed",
        recipient="test@example.com",
        priority=Priority.MEDIUM
    )
    
    low_priority = Notification.create(
        user_id="user_123",
        notification_type=NotificationType.PROMOTIONAL,
        channel=NotificationChannel.EMAIL,
        subject="Sale Alert",
        body="Check out our sale",
        recipient="test@example.com",
        priority=Priority.LOW
    )
    
    # Save all notifications
    repo.save_notification(high_priority)
    repo.save_notification(medium_priority)
    repo.save_notification(low_priority)
    
    # Retrieve and verify
    user_notifications = repo.find_user_notifications("user_123")
    assert len(user_notifications) == 3
    
    # Check priorities
    priorities = [n.priority for n in user_notifications]
    assert Priority.HIGH in priorities
    assert Priority.MEDIUM in priorities
    assert Priority.LOW in priorities
    print("   ✅ Priority handling successful")
    
    # Test pending notifications
    pending = repo.find_pending_notifications()
    assert len(pending) == 3  # All should be pending initially
    
    # Mark one as sent
    high_priority.mark_sent({"id": "sent_123"})
    repo.save_notification(high_priority)
    
    # Check pending again
    pending = repo.find_pending_notifications()
    assert len(pending) == 2  # One less pending
    print("   ✅ Filtering successful")


def run_all_tests():
    """Run all simplified notification tests"""
    print("🚀 Running Simplified Notification Tests")
    print("=" * 60)
    
    try:
        test_notification_repository()
        test_notification_template_rendering()
        test_notification_preferences_logic()
        test_notification_lifecycle()
        test_notification_priority_and_filtering()
        
        print("\n✅ All simplified notification tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
