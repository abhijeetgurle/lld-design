#!/usr/bin/env python3
"""
Unit tests for notification domain entities

Tests the business logic and validation of notification entities
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from datetime import datetime
from core.entities.notification import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationType, NotificationChannel, NotificationStatus, Priority
)

def test_notification_template():
    """Test notification template business logic"""
    print("🧪 Testing NotificationTemplate...")
    
    # Test creating a template
    template = NotificationTemplate(
        template_id="test_template",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        channel=NotificationChannel.EMAIL,
        subject_template="Order #{order_id} Confirmed",
        body_template="Dear {customer_name}, your order #{order_id} is confirmed.",
        variables=['order_id', 'customer_name']
    )
    
    assert template.template_id == "test_template"
    assert template.notification_type == NotificationType.ORDER_CONFIRMATION
    assert template.channel == NotificationChannel.EMAIL
    assert template.is_active == True
    assert 'order_id' in template.variables
    assert 'customer_name' in template.variables
    print("   ✅ Template creation successful")
    
    # Test template rendering with valid variables
    variables = {
        'order_id': 'ORD-123',
        'customer_name': 'John Doe'
    }
    
    subject = template.render_subject(variables)
    body = template.render_body(variables)
    
    assert subject == "Order #ORD-123 Confirmed"
    assert body == "Dear John Doe, your order #ORD-123 is confirmed."
    print("   ✅ Template rendering successful")
    
    # Test template validation with missing variables
    incomplete_variables = {'order_id': 'ORD-123'}  # Missing customer_name
    
    missing = template.validate_variables(incomplete_variables)
    assert 'customer_name' in missing
    assert len(missing) == 1
    print("   ✅ Template validation successful")
    
    # Test that rendering fails with missing variables
    try:
        template.render_body(incomplete_variables)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Missing template variable" in str(e)
        print("   ✅ Missing variable validation successful")


def test_notification_preference():
    """Test notification preference business logic"""
    print("🧪 Testing NotificationPreference...")
    
    # Test creating notification preferences
    preference = NotificationPreference(
        user_id="user_123",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        enabled_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
        is_enabled=True
    )
    
    assert preference.user_id == "user_123"
    assert preference.notification_type == NotificationType.ORDER_CONFIRMATION
    assert NotificationChannel.EMAIL in preference.enabled_channels
    assert NotificationChannel.SMS in preference.enabled_channels
    assert preference.is_enabled == True
    print("   ✅ Preference creation successful")
    
    # Test checking if specific channel is enabled
    assert preference.is_channel_enabled(NotificationChannel.EMAIL) == True
    assert preference.is_channel_enabled(NotificationChannel.SLACK) == False
    print("   ✅ Channel enabled check successful")
    
    # Test that disabled preference blocks all channels
    preference.is_enabled = False
    assert preference.is_channel_enabled(NotificationChannel.EMAIL) == False
    assert preference.is_channel_enabled(NotificationChannel.SMS) == False
    print("   ✅ Disabled preference validation successful")
    
    # Test quiet hours functionality
    preference_with_quiet = NotificationPreference(
        user_id="user_123",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        enabled_channels=[NotificationChannel.EMAIL],
        quiet_hours_start="22:00",
        quiet_hours_end="08:00"
    )
    
    # Test time during quiet hours (23:00)
    quiet_time = datetime.now().replace(hour=23, minute=0)
    assert preference_with_quiet.is_in_quiet_hours(quiet_time) == True
    
    # Test time outside quiet hours (10:00)
    active_time = datetime.now().replace(hour=10, minute=0)
    assert preference_with_quiet.is_in_quiet_hours(active_time) == False
    print("   ✅ Quiet hours functionality successful")


def test_notification():
    """Test notification entity business logic"""
    print("🧪 Testing Notification...")
    
    # Test creating a notification
    notification = Notification.create(
        user_id="user_123",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        channel=NotificationChannel.EMAIL,
        subject="Order Confirmed",
        body="Your order has been confirmed",
        recipient="user@example.com",
        priority=Priority.HIGH
    )
    
    assert notification.user_id == "user_123"
    assert notification.notification_type == NotificationType.ORDER_CONFIRMATION
    assert notification.channel == NotificationChannel.EMAIL
    assert notification.subject == "Order Confirmed"
    assert notification.recipient == "user@example.com"
    assert notification.priority == Priority.HIGH
    assert notification.status == NotificationStatus.PENDING
    assert notification.retry_count == 0
    print("   ✅ Notification creation successful")
    
    # Test marking notification as sent
    provider_response = {"message_id": "msg_123", "status": "sent"}
    notification.mark_sent(provider_response)
    
    assert notification.status == NotificationStatus.SENT
    assert notification.sent_at is not None
    assert notification.provider_response == provider_response
    print("   ✅ Mark sent successful")
    
    # Test marking notification as failed
    notification2 = Notification.create(
        user_id="user_123",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        channel=NotificationChannel.EMAIL,
        subject="Order Confirmed",
        body="Your order has been confirmed",
        recipient="user@example.com"
    )
    
    error_message = "SMTP server unavailable"
    notification2.mark_failed(error_message)
    
    assert notification2.status == NotificationStatus.FAILED
    assert notification2.failed_at is not None
    assert notification2.error_message == error_message
    assert notification2.retry_count == 1
    print("   ✅ Mark failed successful")
    
    # Test retry logic for failed notifications
    notification3 = Notification.create(
        user_id="user_123",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        channel=NotificationChannel.EMAIL,
        subject="Order Confirmed",
        body="Your order has been confirmed",
        recipient="user@example.com"
    )
    
    # Initially cannot retry (not failed)
    assert notification3.can_retry() == False
    
    # After first failure, can retry
    notification3.mark_failed("First failure")
    assert notification3.can_retry() == True
    assert notification3.retry_count == 1
    
    # After max retries, cannot retry
    notification3.retry_count = notification3.max_retries
    assert notification3.can_retry() == False
    print("   ✅ Retry logic successful")
    
    # Test resetting notification for retry
    notification4 = Notification.create(
        user_id="user_123",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        channel=NotificationChannel.EMAIL,
        subject="Order Confirmed",
        body="Your order has been confirmed",
        recipient="user@example.com"
    )
    
    # Mark as failed
    notification4.mark_failed("Network error")
    assert notification4.status == NotificationStatus.FAILED
    assert notification4.error_message == "Network error"
    
    # Reset for retry
    notification4.reset_for_retry()
    assert notification4.status == NotificationStatus.RETRY
    assert notification4.error_message is None
    assert notification4.provider_response is None
    print("   ✅ Reset for retry successful")
    
    # Test reset for retry validation
    notification5 = Notification.create(
        user_id="user_123",
        notification_type=NotificationType.ORDER_CONFIRMATION,
        channel=NotificationChannel.EMAIL,
        subject="Order Confirmed",
        body="Your order has been confirmed",
        recipient="user@example.com"
    )
    
    # Cannot reset if not failed
    try:
        notification5.reset_for_retry()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Notification cannot be retried" in str(e)
        print("   ✅ Reset validation successful")


def run_all_tests():
    """Run all notification entity tests"""
    print("🚀 Running Notification Entity Unit Tests")
    print("=" * 60)
    
    try:
        test_notification_template()
        test_notification_preference()
        test_notification()
        
        print("\n✅ All notification entity tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)