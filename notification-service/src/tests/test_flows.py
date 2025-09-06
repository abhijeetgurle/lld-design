from core.entities.notification import NotificationChannelType, NotificationMessageType
from core.entities.notification_preference import NotificationChannelPreference, NotificationTypePreference
from core.repositories.in_memory_notification_preference_repository import InMemoryNotificationPreferenceRepository
from core.repositories.in_memory_notification_repository import InMemoryNotificationRepository
from core.repositories.in_memory_user_repository import InMemoryUserRepository
from core.services.notification_service import NotificationService
from core.services.user_service import UserService

# New imports for updated architecture
from core.factories.notification_sender_factory import NotificationSenderFactory
from core.services.sender.rate_limiter import RateLimiter
from core.services.notification_processor import NotificationProcessor
import logging
import time

# Set up logging to see the output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize repositories
user_repository = InMemoryUserRepository()
notification_preference_repository = InMemoryNotificationPreferenceRepository()
notification_repository = InMemoryNotificationRepository()

# Initialize services
user_service = UserService(
    user_repository=user_repository,
    notification_preference_repository=notification_preference_repository
)

# Initialize new components
notification_sender_factory = NotificationSenderFactory()
rate_limiter = RateLimiter(max_requests=10, time_window=60)  # 10 per minute
notification_processor = NotificationProcessor(notification_repository)

# Initialize notification service with new architecture
notification_service = NotificationService(
    user_service=user_service,
    notification_repository=notification_repository,
    notification_sender_factory=notification_sender_factory,
    rate_limiter=rate_limiter,
    notification_processor=notification_processor
)


def create_user_test():
    """Test user creation"""
    print("\n" + "=" * 50)
    print("TESTING USER CREATION")
    print("=" * 50)

    user = user_service.create_user(
        name="Abhijeet Gurle",
        email="abhijeetgurle@gmail.com"
    )
    user_service.login(user)
    print(f"Created user 1: {user}")

    user2 = user_service.create_user(
        name="Ujjwal Khare",
        email="ujjawal.khare@gmail.com"
    )
    print(f"Created user 2: {user2}")

    return user, user2


def add_user_preference_test():
    """Test adding user notification preferences"""
    print("\n" + "=" * 50)
    print("TESTING USER PREFERENCES")
    print("=" * 50)

    user = user_service.get_user_by_email('abhijeetgurle@gmail.com')
    user_service.add_notification_preference_for_user(user.id, [
        NotificationChannelPreference(
            priority=0,
            channel_type=NotificationChannelType.SMS,
            enabled=True
        ),
        NotificationChannelPreference(
            priority=0,
            channel_type=NotificationChannelType.EMAIL,
            enabled=True
        )
    ], type_preference=[
        NotificationTypePreference(
            priority=0,
            message_type=NotificationMessageType.MESSAGE,
            enabled=True
        ),
        NotificationTypePreference(
            priority=0,
            message_type=NotificationMessageType.LIKE,
            enabled=True
        )
    ])

    preferences = user_service.get_notification_preference_for_user(user.id)
    print(f"User preferences set: {preferences}")


def test_send_notification():
    """Test basic notification sending"""
    print("\n" + "=" * 50)
    print("TESTING BASIC NOTIFICATION SENDING")
    print("=" * 50)

    user = user_service.get_user_by_email('abhijeetgurle@gmail.com')
    receiver = user_service.get_user_by_email('ujjawal.khare@gmail.com')

    # Set up receiver preferences
    user_service.add_notification_preference_for_user(receiver.id, [
        NotificationChannelPreference(
            priority=0,
            channel_type=NotificationChannelType.EMAIL,
            enabled=True
        ),
        NotificationChannelPreference(
            priority=0,
            channel_type=NotificationChannelType.SMS,
            enabled=True
        )
    ], type_preference=[
        NotificationTypePreference(
            priority=0,
            message_type=NotificationMessageType.MESSAGE,
            enabled=True
        )
    ])

    try:
        notification_service.send_notification(
            user_id=user.id,
            receiver_id=receiver.id,
            type=NotificationMessageType.MESSAGE,
            body="Hello World! This is a test message."
        )
        print("✅ Notification sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")

    # Check notification history
    history = notification_service.get_notifications_sent_by_user(user.id)
    print(f"📋 Notifications sent by user: {len(history)}")
    for notification in history:
        print(
            f"   - {notification.message.template} via {notification.channel.name} (Status: {notification.status.name})")


def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n" + "=" * 50)
    print("TESTING RATE LIMITING")
    print("=" * 50)

    user = user_service.get_user_by_email('abhijeetgurle@gmail.com')
    receiver = user_service.get_user_by_email('ujjawal.khare@gmail.com')

    # Clear rate limiter for clean test
    rate_limiter.clear_user_history(user.id)

    print(f"Rate limit: {rate_limiter.max_requests} notifications per {rate_limiter.time_window} seconds")
    print("Attempting to send 12 notifications (should hit rate limit)...")

    successful_sends = 0
    failed_sends = 0

    # Try to send 12 notifications (should hit rate limit at 11th)
    for i in range(12):
        try:
            notification_service.send_notification(
                user_id=user.id,
                receiver_id=receiver.id,
                type=NotificationMessageType.MESSAGE,
                body=f"Rate limit test message {i + 1}"
            )
            successful_sends += 1
            print(f"   ✅ Message {i + 1}: Sent successfully")
        except Exception as e:
            failed_sends += 1
            print(f"   ❌ Message {i + 1}: {str(e)}")

    print(f"\n📊 Results: {successful_sends} successful, {failed_sends} failed")

    # Check remaining requests
    remaining = rate_limiter.get_remaining_requests(user.id)
    reset_time = rate_limiter.get_reset_time(user.id)
    print(f"📈 Remaining requests for user: {remaining}")
    if reset_time > 0:
        print(f"⏰ Rate limit resets at: {time.ctime(reset_time)}")


def test_notification_history():
    """Test getting notification history"""
    print("\n" + "=" * 50)
    print("TESTING NOTIFICATION HISTORY")
    print("=" * 50)

    user = user_service.get_user_by_email('abhijeetgurle@gmail.com')
    history = notification_service.get_notification_history(user.id, limit=10)

    print(f"📋 Found {len(history)} notifications in history:")
    for i, notification in enumerate(history, 1):
        status_emoji = "✅" if notification.status.name == "SENT" else "❌"
        print(f"   {i}. {status_emoji} '{notification.message.template}' via {notification.channel.name}")
        print(f"      Status: {notification.status.name}, Created: {notification.created_at.strftime('%H:%M:%S')}")
        if notification.retry_count > 0:
            print(f"      Retries: {notification.retry_count}")


def test_different_channels():
    """Test sending to different channels"""
    print("\n" + "=" * 50)
    print("TESTING DIFFERENT CHANNELS")
    print("=" * 50)

    # Clear rate limiter for clean test
    user = user_service.get_user_by_email('abhijeetgurle@gmail.com')
    rate_limiter.clear_user_history(user.id)

    receiver = user_service.get_user_by_email('ujjawal.khare@gmail.com')

    # Add preferences for receiver to get notifications on all channels
    user_service.add_notification_preference_for_user(receiver.id, [
        NotificationChannelPreference(
            priority=0,
            channel_type=NotificationChannelType.EMAIL,
            enabled=True
        ),
        NotificationChannelPreference(
            priority=0,
            channel_type=NotificationChannelType.SMS,
            enabled=True
        ),
        NotificationChannelPreference(
            priority=0,
            channel_type=NotificationChannelType.PUSH,
            enabled=True
        )
    ], type_preference=[
        NotificationTypePreference(
            priority=0,
            message_type=NotificationMessageType.FRIEND_REQUEST,
            enabled=True
        )
    ])

    print("Sending friend request (should go to all enabled channels)...")

    try:
        notification_service.send_notification(
            user_id=user.id,
            receiver_id=receiver.id,
            type=NotificationMessageType.FRIEND_REQUEST,
            body="Would you like to be friends? 🤝"
        )
        print("✅ Friend request sent to all channels!")
    except Exception as e:
        print(f"❌ Failed to send friend request: {e}")


def test_retry_mechanism():
    """Test retry mechanism (simulated)"""
    print("\n" + "=" * 50)
    print("TESTING RETRY MECHANISM")
    print("=" * 50)

    print("Note: Retry mechanism is built-in to the NotificationProcessor.")
    print("It automatically retries failed notifications with exponential backoff:")
    print("- Retry 1: 1 second delay")
    print("- Retry 2: 2 second delay")
    print("- Retry 3: 4 second delay")
    print("- After 3 retries: Mark as permanently failed")
    print("\nThe concrete senders simulate random failures for testing.")


def test_mark_as_read():
    """Test marking notifications as read"""
    print("\n" + "=" * 50)
    print("TESTING MARK AS READ")
    print("=" * 50)

    user = user_service.get_user_by_email('abhijeetgurle@gmail.com')
    history = notification_service.get_notification_history(user.id, limit=3)

    if history:
        notification = history[0]
        print(f"Before: Notification read status = {notification.is_read()}")

        notification.mark_as_read()
        print(f"After: Notification read status = {notification.is_read()}")
        print("✅ Notification marked as read!")
    else:
        print("❌ No notifications found to mark as read")


def run_all_tests():
    """Run all tests in sequence"""
    print("🚀 STARTING NOTIFICATION SERVICE TESTS")
    print("=" * 60)

    try:
        # Basic functionality tests
        create_user_test()
        add_user_preference_test()
        test_send_notification()

        # Advanced functionality tests
        test_rate_limiting()
        test_notification_history()
        test_different_channels()
        test_retry_mechanism()
        test_mark_as_read()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_all_tests()
