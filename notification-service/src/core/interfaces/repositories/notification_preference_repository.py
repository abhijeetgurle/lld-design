from abc import ABC, abstractmethod

from core.entities.notification_preference import NotificationPreference


class NotificationPreferenceRepository(ABC):
    @abstractmethod
    def save(self, notification_preference: NotificationPreference):
        pass

    @abstractmethod
    def delete(self, notification_preference: NotificationPreference):
        pass

    @abstractmethod
    def get_notification_preference_for_user_by_id(self, user_id: str) -> NotificationPreference:
        pass