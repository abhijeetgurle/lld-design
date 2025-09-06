from typing import List

from core.entities.notification import Notification
from core.interfaces.repositories.notification_repository import NotificationRepository


class InMemoryNotificationRepository(NotificationRepository):
    def __init__(self):
        self.notifications: list[Notification] = []

    def save(self, notification: Notification):
        self.notifications.append(notification)

    def delete(self, notification: Notification):
        self.notifications.remove(notification)

    def get_notifications_for_user_by_id(self, user_id: str) -> List[Notification]:
        res = []
        for notification in self.notifications:
            if notification.source.id == user_id:
                res.append(notification)

        return res