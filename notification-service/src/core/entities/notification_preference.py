from dataclasses import dataclass, field

from core.entities.notification import NotificationChannelType, NotificationMessageType
from core.entities.user import User

@dataclass
class NotificationChannelPreference:
    priority: int = 0
    channel_type: NotificationChannelType = NotificationChannelType.SMS
    enabled: bool = True

@dataclass
class NotificationTypePreference:
    priority: int = 0
    message_type: NotificationMessageType = NotificationMessageType.MESSAGE
    enabled: bool = True

@dataclass
class NotificationPreference:
    user: User
    channel_preference: list[NotificationChannelPreference] = None
    type_preference: list[NotificationTypePreference] = None

    def __post_init__(self):
        if self.user is None:
            raise ValueError("user is required")

        if self.channel_preference is None:
            self.channel_preference = [
            NotificationChannelPreference(0, NotificationChannelType.SMS, True),
            NotificationChannelPreference(0, NotificationChannelType.EMAIL, True),
            NotificationChannelPreference(0, NotificationChannelType.PUSH, True),
        ]

        if self.type_preference is None:
            self.type_preference = [
                NotificationTypePreference(0, NotificationMessageType.MESSAGE, True),
                NotificationTypePreference(0, NotificationMessageType.FRIEND_REQUEST, True),
                NotificationTypePreference(0, NotificationMessageType.LIKE, True),
                NotificationTypePreference(0, NotificationMessageType.COMMENT, True),
            ]

    def update_channel_preference(self, channel_preference: list[NotificationChannelPreference]):
        self.channel_preference = channel_preference

    def update_type_preference(self, type_preference: list[NotificationTypePreference]):
        self.type_preference = type_preference