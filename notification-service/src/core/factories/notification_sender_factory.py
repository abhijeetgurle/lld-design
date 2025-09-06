from typing import Dict
from core.entities.notification import NotificationChannelType
from core.interfaces.notification_sender import NotificationSender
from core.services.sender.email_sender import EmailSender
from core.services.sender.sms_sender import SMSSender
from core.services.sender.push_sender import PushSender


class NotificationSenderFactory:
    """Factory class for creating notification senders using Factory pattern"""

    def __init__(self):
        self._senders: Dict[NotificationChannelType, NotificationSender] = {}
        self._initialize_senders()

    def _initialize_senders(self):
        """Initialize all available notification senders"""
        self._senders[NotificationChannelType.EMAIL] = EmailSender()
        self._senders[NotificationChannelType.SMS] = SMSSender()
        self._senders[NotificationChannelType.PUSH] = PushSender()

    def get_sender(self, channel_type: NotificationChannelType) -> NotificationSender:
        """
        Get appropriate notification sender for the given channel type

        Args:
            channel_type: The type of notification channel

        Returns:
            NotificationSender: The appropriate sender implementation

        Raises:
            ValueError: If channel type is not supported
        """
        if channel_type not in self._senders:
            raise ValueError(f"Unsupported notification channel: {channel_type}")

        return self._senders[channel_type]

    def get_all_senders(self) -> Dict[NotificationChannelType, NotificationSender]:
        """Get all available notification senders"""
        return self._senders.copy()

    def register_sender(self, channel_type: NotificationChannelType, sender: NotificationSender):
        """Register a new notification sender (for extensibility)"""
        self._senders[channel_type] = sender