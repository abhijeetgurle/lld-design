from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid

class NotificationType(Enum):
    ORDER_CONFIRMATION = "ORDER_CONFIRMATION"
    ORDER_SHIPPED = "ORDER_SHIPPED"
    ORDER_DELIVERED = "ORDER_DELIVERED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    REFUND_PROCESSED = "REFUND_PROCESSED"
    LOW_STOCK_ALERT = "LOW_STOCK_ALERT"
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    PASSWORD_RESET = "PASSWORD_RESET"
    PROMOTIONAL = "PROMOTIONAL"

class NotificationChannel(Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"
    IN_APP = "IN_APP"
    SLACK = "SLACK"
    WEBHOOK = "WEBHOOK"

class NotificationStatus(Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETRY = "RETRY"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class NotificationTemplate:
    """Template for different types of notifications"""
    template_id: str
    notification_type: NotificationType
    channel: NotificationChannel
    subject_template: str
    body_template: str
    language: str = "en"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    variables: List[str] = field(default_factory=list)
    
    def render_subject(self, variables: Dict[str, Any]) -> str:
        """Render subject with variable substitution"""
        return self._render_template(self.subject_template, variables)
    
    def render_body(self, variables: Dict[str, Any]) -> str:
        """Render body with variable substitution"""
        return self._render_template(self.body_template, variables)
    
    def validate_variables(self, variables: Dict[str, Any]) -> List[str]:
        """Validate that all required variables are provided"""
        missing = []
        for required_var in self.variables:
            if required_var not in variables:
                missing.append(required_var)
        return missing
    
    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Private method to render template with variables"""
        try:
            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")

@dataclass
class NotificationPreference:
    """User preferences for different types of notifications"""
    user_id: str
    notification_type: NotificationType
    enabled_channels: List[NotificationChannel]
    is_enabled: bool = True
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: str = "UTC"
    
    def is_channel_enabled(self, channel: NotificationChannel) -> bool:
        """Check if user has enabled this channel for this notification type"""
        return self.is_enabled and channel in self.enabled_channels
    
    def is_in_quiet_hours(self, current_time: datetime = None) -> bool:
        """Check if current time is in user's quiet hours"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        if current_time is None:
            current_time = datetime.now()
        
        current_hour = current_time.hour
        start_hour = int(self.quiet_hours_start.split(':')[0])
        end_hour = int(self.quiet_hours_end.split(':')[0])
        
        if start_hour <= end_hour:
            return start_hour <= current_hour <= end_hour
        else:
            return current_hour >= start_hour or current_hour <= end_hour

@dataclass
class Notification:
    """Individual notification instance"""
    notification_id: str
    user_id: str
    notification_type: NotificationType
    channel: NotificationChannel
    subject: str
    body: str
    status: NotificationStatus = NotificationStatus.PENDING
    priority: Priority = Priority.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    recipient: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    provider_response: Optional[Dict] = None
    
    @classmethod
    def create(cls, user_id: str, notification_type: NotificationType, 
               channel: NotificationChannel, subject: str, body: str,
               recipient: str, priority: Priority = Priority.MEDIUM) -> 'Notification':
        """Factory method for creating notifications"""
        return cls(
            notification_id=str(uuid.uuid4()),
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
            subject=subject,
            body=body,
            recipient=recipient,
            priority=priority
        )
    
    def mark_sent(self, provider_response: Dict = None) -> None:
        """Mark notification as sent"""
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now()
        self.provider_response = provider_response
    
    def mark_delivered(self) -> None:
        """Mark notification as delivered"""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.now()
    
    def mark_failed(self, error_message: str, provider_response: Dict = None) -> None:
        """Mark notification as failed"""
        self.status = NotificationStatus.FAILED
        self.failed_at = datetime.now()
        self.error_message = error_message
        self.provider_response = provider_response
        self.retry_count += 1
    
    def can_retry(self) -> bool:
        """Check if notification can be retried"""
        return (self.status == NotificationStatus.FAILED and 
                self.retry_count < self.max_retries)
    
    def reset_for_retry(self) -> None:
        """Reset notification for retry"""
        if not self.can_retry():
            raise ValueError("Notification cannot be retried")
        
        self.status = NotificationStatus.RETRY
        self.error_message = None
        self.provider_response = None
