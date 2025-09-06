from typing import Optional

from core.entities.notification_preference import NotificationPreference
from core.interfaces.repositories.notification_preference_repository import NotificationPreferenceRepository


class InMemoryNotificationPreferenceRepository(NotificationPreferenceRepository):
    def __init__(self):
        self.notification_preferences: list[NotificationPreference] = []

    def save(self, notification_preference: NotificationPreference):
        self.notification_preferences.append(notification_preference)

    def delete(self, notification_preference: NotificationPreference):
        self.notification_preferences.remove(notification_preference)

    def get_notification_preference_for_user_by_id(self, user_id: str) -> Optional[NotificationPreference]:
        for notification_preference in self.notification_preferences:
            if notification_preference.user.id == user_id:
                return notification_preference

        return None