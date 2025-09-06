from abc import ABC, abstractmethod

from core.entities.notification import Notification
from core.entities.user import User


class NotificationRepository(ABC):
    @abstractmethod
    def save(self, notification: Notification):
        pass

    @abstractmethod
    def delete(self, notification: Notification):
        pass

    @abstractmethod
    def get_notifications_for_user_by_id(self, user_id: str):
        pass