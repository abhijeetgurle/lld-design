import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.entities.user import User


class NotificationChannelType(Enum):
    EMAIL = 0
    SMS = 1
    PUSH = 2

class NotificationMessageType(Enum):
    MESSAGE = 0
    FRIEND_REQUEST = 1
    LIKE = 2
    COMMENT = 3

class NotificationStatus(Enum):
    PENDING = 0
    SENT = 1
    DELIVERED = 2
    FAILED = 3

@dataclass
class NotificationMessage:
    template: str
    type: NotificationMessageType = NotificationMessageType.MESSAGE

    def update_template(self, template: str):
        self.template = template

    def get_template(self):
        return self.template

    def set_template_with_values(self, values: dict[str, str]) -> str:
        # fill template with values and return
        return self.template.format(**values)



@dataclass
class Notification:
    source: User
    dest: User
    channel: NotificationChannelType
    message: NotificationMessage
    status: NotificationStatus = field(default=NotificationStatus.PENDING)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now())
    sent_at: datetime = None
    last_retry_at: datetime = None
    retry_count: int = 0
    read_status: bool = False

    def __post_init__(self):
        if self.channel is None:
            raise ValueError("channel cannot be None")

        if self.message is None:
            raise ValueError("message cannot be None")

        if self.source is None:
            raise ValueError("Source for notification cannot be empty")

        if self.dest is None:
            raise ValueError("Dest for notification cannot be empty")

    def update_channel(self, channel: NotificationChannelType):
        self.channel = channel

    def update_message(self, message: NotificationMessage):
        self.message = message

    def get_formatted_message(self, values: dict[str, str]) -> str:
        return self.message.set_template_with_values(values)

    def update_notification_status(self, status: NotificationStatus):
        self.status = status

    def update_source(self, source: User):
        self.source = source

    def update_dest(self, dest: User):
        self.dest = dest

    def update_status(self, status: NotificationStatus):
        self.status = status
        if self.status is NotificationStatus.SENT:
            self.sent_at = datetime.now()

    def update_last_retry_at(self, last_retry_at: datetime):
        self.last_retry_at = last_retry_at

    def update_retry_count(self, retry_count: int):
        self.retry_count = retry_count

    def mark_as_read(self):
        """Mark the notification as read"""
        self.read_status = True

    def is_read(self) -> bool:
        """Check if notification has been read"""
        return self.read_status