from typing import Dict, List, Optional
from threading import Lock

from core.interfaces.repositories.notification_repository import NotificationRepository
from core.entities.notification import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationType, NotificationChannel, NotificationStatus
)


class InMemoryNotificationRepository(NotificationRepository):
    """In-memory implementation for testing and demos"""
    
    def __init__(self):
        self._notifications: Dict[str, Notification] = {}
        self._templates: Dict[str, NotificationTemplate] = {}
        self._preferences: Dict[str, NotificationPreference] = {}
        self._lock = Lock()
    
    def save_notification(self, notification: Notification) -> Notification:
        with self._lock:
            self._notifications[notification.notification_id] = notification
            return notification
    
    def find_notification(self, notification_id: str) -> Optional[Notification]:
        return self._notifications.get(notification_id)
    
    def find_user_notifications(self, user_id: str, limit: int = 50) -> List[Notification]:
        user_notifications = [
            notif for notif in self._notifications.values()
            if notif.user_id == user_id
        ]
        user_notifications.sort(key=lambda x: x.created_at, reverse=True)
        return user_notifications[:limit]
    
    def find_pending_notifications(self) -> List[Notification]:
        return [
            notif for notif in self._notifications.values()
            if notif.status == NotificationStatus.PENDING
        ]
    
    def find_failed_notifications(self) -> List[Notification]:
        return [
            notif for notif in self._notifications.values()
            if notif.status == NotificationStatus.FAILED
        ]
    
    def save_template(self, template: NotificationTemplate) -> NotificationTemplate:
        with self._lock:
            key = f"{template.notification_type.value}_{template.channel.value}_{template.language}"
            self._templates[key] = template
            return template
    
    def find_template(self, notification_type: NotificationType, 
                     channel: NotificationChannel, language: str = "en") -> Optional[NotificationTemplate]:
        key = f"{notification_type.value}_{channel.value}_{language}"
        return self._templates.get(key)
    
    def save_preference(self, preference: NotificationPreference) -> NotificationPreference:
        with self._lock:
            key = f"{preference.user_id}_{preference.notification_type.value}"
            self._preferences[key] = preference
            return preference
    
    def find_user_preference(self, user_id: str, 
                           notification_type: NotificationType) -> Optional[NotificationPreference]:
        key = f"{user_id}_{notification_type.value}"
        return self._preferences.get(key)
    
    def clear_all(self):
        """Clear all data (useful for testing)"""
        with self._lock:
            self._notifications.clear()
            self._templates.clear()
            self._preferences.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get repository statistics"""
        return {
            'total_notifications': len(self._notifications),
            'total_templates': len(self._templates),
            'total_preferences': len(self._preferences),
            'pending_notifications': len(self.find_pending_notifications()),
            'failed_notifications': len(self.find_failed_notifications())
        }
