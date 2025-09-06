from abc import ABC, abstractmethod
from core.entities.notification import Notification


class NotificationSender(ABC):
    """Abstract base class for notification senders using Strategy pattern"""

    @abstractmethod
    def send(self, notification: Notification) -> bool:
        """
        Send a notification through specific channel

        Args:
            notification: The notification to send

        Returns:
            bool: True if sent successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_channel_type(self) -> str:
        """Return the channel type this sender handles"""
        pass