from typing import List

from core.entities.notification import NotificationMessageType, Notification, NotificationMessage, NotificationStatus
from core.factories.notification_sender_factory import NotificationSenderFactory
from core.interfaces.repositories.notification_repository import NotificationRepository
from core.services.notification_processor import NotificationProcessor
from core.services.sender.rate_limiter import RateLimiter
from core.services.user_service import UserService


class NotificationService:
    def __init__(self, user_service: UserService,
                notification_repository: NotificationRepository,
                notification_sender_factory: NotificationSenderFactory,
                rate_limiter: RateLimiter,
                notification_processor: NotificationProcessor):
        self.user_service = user_service
        self.notification_sender_factory = notification_sender_factory
        self.notification_repository = notification_repository
        self.rate_limiter = rate_limiter
        self.notification_processor = notification_processor


    def send_notification(self, user_id: str, receiver_id: str, type: NotificationMessageType, body: str):
        source_user = self.user_service.get_user_by_id(user_id)
        destination_user = self.user_service.get_user_by_id(receiver_id)

        if not self.rate_limiter.can_send(user_id):
            raise Exception(f"Rate limit exceeded for user {user_id}")

        notification_preference = self.user_service.get_notification_preference_for_user(user_id)
        if notification_preference is None:
            return

        type_enabled = False
        for notification_type in notification_preference.type_preference:
            if notification_type.message_type == type and notification_type.enabled:
                type_enabled = True
                break

        if not type_enabled:
            return

        for channel_pref in notification_preference.channel_preference:
            if channel_pref.enabled:
                # Create notification with proper channel type
                notification = Notification(
                    source=source_user,
                    dest=destination_user,
                    channel=channel_pref.channel_type,  # ← Use channel_type, not the preference object
                    message=NotificationMessage(type=type, template=body)
                )

                # Get appropriate sender and process with retry logic
                sender = self.notification_sender_factory.get_sender(channel_pref.channel_type)
                success = self.notification_processor.process_notification(notification, sender)

                if success:
                    self.notification_repository.save(notification)

    def get_notifications_sent_by_user(self, user_id: str) -> List[Notification]:
        return self.notification_repository.get_notifications_for_user_by_id(user_id)


    def get_notification_history(self, user_id: str, limit: int = 50) -> List[Notification]:
        """Get notification history for a user"""
        return self.notification_repository.get_notifications_for_user_by_id(user_id)[:limit]

    def mark_as_read(self, user_id: str, notification_id: str):
        """Mark a notification as read"""
        # You'll need to add a method to repository to find by notification_id
        # notification = self.notification_repository.get_by_id(notification_id)
        # if notification and notification.dest.id == user_id:
        #     notification.mark_as_read()
        #     self.notification_repository.save(notification)
        pass