from abc import ABC, abstractmethod
from typing import List, Optional
from core.entities.notification import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationType, NotificationChannel
)

class NotificationRepository(ABC):
    """Repository interface for notification data"""
    
    @abstractmethod
    def save_notification(self, notification: Notification) -> Notification:
        pass
    
    @abstractmethod
    def find_notification(self, notification_id: str) -> Optional[Notification]:
        pass
    
    @abstractmethod
    def find_user_notifications(self, user_id: str, limit: int = 50) -> List[Notification]:
        pass
    
    @abstractmethod
    def find_pending_notifications(self) -> List[Notification]:
        pass
    
    @abstractmethod
    def find_failed_notifications(self) -> List[Notification]:
        pass
    
    @abstractmethod
    def save_template(self, template: NotificationTemplate) -> NotificationTemplate:
        pass
    
    @abstractmethod
    def find_template(self, notification_type: NotificationType, 
                     channel: NotificationChannel, language: str = "en") -> Optional[NotificationTemplate]:
        pass
    
    @abstractmethod
    def save_preference(self, preference: NotificationPreference) -> NotificationPreference:
        pass
    
    @abstractmethod
    def find_user_preference(self, user_id: str, 
                           notification_type: NotificationType) -> Optional[NotificationPreference]:
        pass
