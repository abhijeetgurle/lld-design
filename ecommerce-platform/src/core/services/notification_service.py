from typing import Dict, List, Optional, Any
import logging
import threading
import time
from queue import PriorityQueue, Empty
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from dataclasses import dataclass
import uuid

from core.entities.notification import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationType, NotificationChannel, NotificationStatus, Priority
)
from core.interfaces.repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)

# Channel interfaces and implementations
@dataclass
class ChannelResponse:
    """Response from notification channel"""
    success: bool
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    provider_response: Optional[Dict] = None
    is_retriable: bool = True

class NotificationChannelInterface(ABC):
    """Abstract interface for notification channels"""
    
    @abstractmethod
    def get_channel_type(self) -> NotificationChannel:
        pass
    
    @abstractmethod
    def send(self, recipient: str, subject: str, body: str, 
             metadata: Dict[str, Any] = None) -> ChannelResponse:
        pass
    
    @abstractmethod
    def is_healthy(self) -> bool:
        pass
    
    @abstractmethod
    def get_rate_limit(self) -> Optional[int]:
        pass

# Channel implementations
class EmailNotificationChannel(NotificationChannelInterface):
    """Email notification channel implementation"""
    
    def __init__(self, smtp_config: Dict[str, str]):
        self.smtp_host = smtp_config.get('host', 'smtp.gmail.com')
        self.from_email = smtp_config.get('from_email', 'noreply@ecommerce.com')
    
    def get_channel_type(self) -> NotificationChannel:
        return NotificationChannel.EMAIL
    
    def send(self, recipient: str, subject: str, body: str, 
             metadata: Dict[str, Any] = None) -> ChannelResponse:
        try:
            message_id = f"email_{uuid.uuid4().hex[:8]}"
            
            print(f"📧 EMAIL SENT")
            print(f"To: {recipient}")
            print(f"Subject: {subject}")
            print(f"Body: {body[:100]}{'...' if len(body) > 100 else ''}")
            print("-" * 50)
            
            return ChannelResponse(
                success=True,
                message_id=message_id,
                provider_response={'status': 'sent', 'recipient': recipient}
            )
        except Exception as e:
            return ChannelResponse(success=False, error_message=str(e))
    
    def is_healthy(self) -> bool:
        return True
    
    def get_rate_limit(self) -> Optional[int]:
        return 100

class SMSNotificationChannel(NotificationChannelInterface):
    """SMS notification channel"""
    
    def __init__(self, twilio_config: Dict[str, str]):
        self.from_number = twilio_config.get('from_number')
    
    def get_channel_type(self) -> NotificationChannel:
        return NotificationChannel.SMS
    
    def send(self, recipient: str, subject: str, body: str, 
             metadata: Dict[str, Any] = None) -> ChannelResponse:
        try:
            message_id = f"sms_{uuid.uuid4().hex[:8]}"
            
            print(f"📱 SMS SENT")
            print(f"To: {recipient}")
            print(f"Message: {body}")
            print("-" * 50)
            
            return ChannelResponse(success=True, message_id=message_id)
        except Exception as e:
            return ChannelResponse(success=False, error_message=str(e))
    
    def is_healthy(self) -> bool:
        return True
    
    def get_rate_limit(self) -> Optional[int]:
        return 60

class SlackNotificationChannel(NotificationChannelInterface):
    """Slack notification channel"""
    
    def __init__(self, slack_config: Dict[str, str]):
        self.channel = slack_config.get('channel', '#alerts')
    
    def get_channel_type(self) -> NotificationChannel:
        return NotificationChannel.SLACK
    
    def send(self, recipient: str, subject: str, body: str, 
             metadata: Dict[str, Any] = None) -> ChannelResponse:
        try:
            message_id = f"slack_{uuid.uuid4().hex[:8]}"
            
            print(f"💬 SLACK NOTIFICATION")
            print(f"Channel: {self.channel}")
            print(f"Subject: {subject}")
            print(f"Message: {body}")
            print("-" * 50)
            
            return ChannelResponse(success=True, message_id=message_id)
        except Exception as e:
            return ChannelResponse(success=False, error_message=str(e))
    
    def is_healthy(self) -> bool:
        return True
    
    def get_rate_limit(self) -> Optional[int]:
        return 300

# Service exceptions
class NotificationServiceException(Exception):
    pass

class TemplateNotFoundException(NotificationServiceException):
    pass

class NotificationService:
    """Complete notification service implementation"""
    
    def __init__(self, notification_repository: NotificationRepository, user_service=None):
        self.notification_repo = notification_repository
        self.user_service = user_service
        self.channels: Dict[NotificationChannel, NotificationChannelInterface] = {}
        self.notification_queue = PriorityQueue()
        self.processing_thread = None
        self.stop_processing = threading.Event()
        self.rate_limits: Dict[NotificationChannel, Dict] = {}
        self.processing_enabled = True
        
        self._initialize_default_templates()
        self._start_background_processing()
    
    def register_channel(self, channel: NotificationChannelInterface) -> None:
        """Register a notification channel"""
        channel_type = channel.get_channel_type()
        self.channels[channel_type] = channel
        
        rate_limit = channel.get_rate_limit()
        if rate_limit:
            self.rate_limits[channel_type] = {
                'limit': rate_limit,
                'window_start': datetime.now(),
                'count': 0
            }
        
        logger.info(f"Registered notification channel: {channel_type.value}")
    
    def send_notification(self, user_id: str, notification_type: NotificationType,
                         variables: Dict[str, Any], priority: Priority = Priority.MEDIUM,
                         override_preferences: bool = False) -> List[Notification]:
        """Send notification to user across enabled channels"""
        notifications = []
        
        try:
            if not override_preferences:
                preference = self.notification_repo.find_user_preference(user_id, notification_type)
                if preference and not preference.is_enabled:
                    return notifications
                
                if preference and preference.is_in_quiet_hours():
                    return notifications
                
                enabled_channels = preference.enabled_channels if preference else [NotificationChannel.EMAIL]
            else:
                enabled_channels = list(self.channels.keys())
            
            for channel in enabled_channels:
                if channel not in self.channels:
                    continue
                
                try:
                    notification = self._create_notification(
                        user_id, notification_type, channel, variables, priority
                    )
                    
                    if notification:
                        saved_notification = self.notification_repo.save_notification(notification)
                        notifications.append(saved_notification)
                        self._queue_notification(saved_notification)
                        
                except Exception as e:
                    logger.error(f"Failed to create notification for {channel.value}: {e}")
            
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            raise NotificationServiceException(f"Notification sending failed: {str(e)}")
    
    # Business-specific notification methods
    def send_order_confirmation(self, order, customer) -> List[Notification]:
        """Send order confirmation notification"""
        variables = {
            'customer_name': customer.name,
            'order_id': order.order_id,
            'order_total': str(order.total_amount),
            'order_date': order.created_at.strftime('%Y-%m-%d %H:%M'),
            'item_count': len(order.items),
            'estimated_delivery': '3-5 business days'
        }
        
        return self.send_notification(
            user_id=customer.user_id,
            notification_type=NotificationType.ORDER_CONFIRMATION,
            variables=variables,
            priority=Priority.HIGH
        )
    
    def send_shipping_update(self, order, tracking_id: str) -> List[Notification]:
        """Send shipping notification"""
        variables = {
            'order_id': order.order_id,
            'tracking_id': tracking_id,
            'shipping_date': datetime.now().strftime('%Y-%m-%d'),
            'carrier': 'FedEx',
            'estimated_delivery': '2-3 business days'
        }
        
        return self.send_notification(
            user_id=order.customer_id,
            notification_type=NotificationType.ORDER_SHIPPED,
            variables=variables,
            priority=Priority.MEDIUM
        )
    
    def send_payment_success(self, payment) -> List[Notification]:
        """Send payment success notification"""
        variables = {
            'payment_id': payment.payment_id,
            'amount': str(payment.amount),
            'payment_method': payment.method.value,
            'transaction_id': payment.transaction_id or 'N/A',
            'payment_date': payment.processed_at.strftime('%Y-%m-%d %H:%M') if payment.processed_at else 'N/A'
        }
        
        return self.send_notification(
            user_id=payment.customer_id,
            notification_type=NotificationType.PAYMENT_SUCCESS,
            variables=variables,
            priority=Priority.HIGH
        )
    
    def send_payment_failure(self, payment, error_reason: str) -> List[Notification]:
        """Send payment failure notification"""
        variables = {
            'payment_id': payment.payment_id,
            'amount': str(payment.amount),
            'payment_method': payment.method.value,
            'error_reason': error_reason,
            'retry_url': f'https://example.com/retry-payment/{payment.payment_id}'
        }
        
        return self.send_notification(
            user_id=payment.customer_id,
            notification_type=NotificationType.PAYMENT_FAILED,
            variables=variables,
            priority=Priority.URGENT
        )
    
    def send_low_stock_alert(self, low_stock_products: List[Dict]) -> List[Notification]:
        """Send low stock alert to administrators"""
        product_list = '\n'.join([
            f"- {product['product_id']}: {product['available_quantity']} remaining"
            for product in low_stock_products
        ])
        
        variables = {
            'alert_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'product_count': len(low_stock_products),
            'product_list': product_list,
            'dashboard_url': 'https://admin.example.com/inventory'
        }
        
        admin_user_ids = ['admin_1', 'admin_2']
        notifications = []
        for admin_id in admin_user_ids:
            admin_notifications = self.send_notification(
                user_id=admin_id,
                notification_type=NotificationType.LOW_STOCK_ALERT,
                variables=variables,
                priority=Priority.HIGH,
                override_preferences=True
            )
            notifications.extend(admin_notifications)
        
        return notifications
    
    def get_user_notifications(self, user_id: str, limit: int = 50) -> List[Notification]:
        """Get notification history for user"""
        return self.notification_repo.find_user_notifications(user_id, limit)
    
    def update_user_preferences(self, user_id: str, notification_type: NotificationType,
                              enabled_channels: List[NotificationChannel],
                              is_enabled: bool = True) -> NotificationPreference:
        """Update user notification preferences"""
        preference = NotificationPreference(
            user_id=user_id,
            notification_type=notification_type,
            enabled_channels=enabled_channels,
            is_enabled=is_enabled
        )
        
        return self.notification_repo.save_preference(preference)
    
    def _create_notification(self, user_id: str, notification_type: NotificationType,
                           channel: NotificationChannel, variables: Dict[str, Any],
                           priority: Priority) -> Optional[Notification]:
        """Create notification from template"""
        template = self.notification_repo.find_template(notification_type, channel)
        if not template:
            raise TemplateNotFoundException(
                f"Template not found for {notification_type.value} on {channel.value}"
            )
        
        missing_vars = template.validate_variables(variables)
        if missing_vars:
            raise ValueError(f"Missing template variables: {missing_vars}")
        
        try:
            subject = template.render_subject(variables)
            body = template.render_body(variables)
        except Exception as e:
            raise ValueError(f"Template rendering failed: {e}")
        
        recipient = self._get_user_recipient_info(user_id, channel)
        if not recipient:
            return None
        
        notification = Notification.create(
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
            subject=subject,
            body=body,
            recipient=recipient,
            priority=priority
        )
        
        return notification
    
    def _queue_notification(self, notification: Notification) -> None:
        """Queue notification for background processing"""
        priority_value = 5 - notification.priority.value
        timestamp = notification.created_at.timestamp()
        self.notification_queue.put((priority_value, timestamp, notification))
    
    def _process_notification(self, notification: Notification) -> bool:
        """Process single notification"""
        channel = self.channels.get(notification.channel)
        if not channel:
            notification.mark_failed(f"Channel {notification.channel.value} not available")
            self.notification_repo.save_notification(notification)
            return False
        
        if not self._check_rate_limit(notification.channel):
            self._queue_notification(notification)
            return False
        
        try:
            response = channel.send(
                recipient=notification.recipient,
                subject=notification.subject,
                body=notification.body,
                metadata=notification.metadata
            )
            
            if response.success:
                notification.mark_sent(response.provider_response)
                success = True
            else:
                notification.mark_failed(response.error_message, response.provider_response)
                success = False
            
            self._update_rate_limit_counter(notification.channel)
            self.notification_repo.save_notification(notification)
            
            return success
            
        except Exception as e:
            notification.mark_failed(str(e))
            self.notification_repo.save_notification(notification)
            return False
    
    def _background_processor(self) -> None:
        """Background thread for processing notifications"""
        while not self.stop_processing.is_set():
            try:
                try:
                    priority, timestamp, notification = self.notification_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                self._process_notification(notification)
                self.notification_queue.task_done()
                
            except Exception as e:
                logger.error(f"Background processor error: {e}")
                time.sleep(1)
    
    def _start_background_processing(self) -> None:
        """Start background processing thread"""
        if self.processing_enabled:
            self.processing_thread = threading.Thread(
                target=self._background_processor,
                daemon=True
            )
            self.processing_thread.start()
    
    def _check_rate_limit(self, channel: NotificationChannel) -> bool:
        """Check if channel is within rate limit"""
        if channel not in self.rate_limits:
            return True
        
        limit_info = self.rate_limits[channel]
        now = datetime.now()
        
        if (now - limit_info['window_start']).total_seconds() >= 60:
            limit_info['window_start'] = now
            limit_info['count'] = 0
        
        return limit_info['count'] < limit_info['limit']
    
    def _update_rate_limit_counter(self, channel: NotificationChannel) -> None:
        """Update rate limit counter after sending"""
        if channel in self.rate_limits:
            self.rate_limits[channel]['count'] += 1
    
    def _get_user_recipient_info(self, user_id: str, channel: NotificationChannel) -> Optional[str]:
        """Get recipient information for user and channel"""
        if self.user_service:
            user = self.user_service.get_user_by_id(user_id)
            if user:
                if channel == NotificationChannel.EMAIL:
                    return user.email
        
        # Fallback for demo
        if channel == NotificationChannel.EMAIL:
            return f"user_{user_id}@example.com"
        elif channel == NotificationChannel.SMS:
            return f"+1234567890"
        
        return f"user_{user_id}"
    
    def _initialize_default_templates(self) -> None:
        """Initialize default notification templates"""
        default_templates = [
            NotificationTemplate(
                template_id="order_confirmation_email",
                notification_type=NotificationType.ORDER_CONFIRMATION,
                channel=NotificationChannel.EMAIL,
                subject_template="Order Confirmed - #{order_id}",
                body_template="""Dear {customer_name},

Thank you for your order! Your order #{order_id} has been confirmed.

Order Details:
- Order Total: {order_total}
- Items: {item_count}
- Order Date: {order_date}
- Estimated Delivery: {estimated_delivery}

Thank you for shopping with us!""",
                variables=['customer_name', 'order_id', 'order_total', 'item_count', 'order_date', 'estimated_delivery']
            ),
            
            NotificationTemplate(
                template_id="payment_success_email",
                notification_type=NotificationType.PAYMENT_SUCCESS,
                channel=NotificationChannel.EMAIL,
                subject_template="Payment Successful - {payment_id}",
                body_template="""Your payment has been processed successfully!

Payment Details:
- Payment ID: {payment_id}
- Amount: {amount}
- Payment Method: {payment_method}
- Transaction ID: {transaction_id}
- Payment Date: {payment_date}

Thank you for your business!""",
                variables=['payment_id', 'amount', 'payment_method', 'transaction_id', 'payment_date']
            ),
            
            NotificationTemplate(
                template_id="low_stock_alert_email",
                notification_type=NotificationType.LOW_STOCK_ALERT,
                channel=NotificationChannel.EMAIL,
                subject_template="Low Stock Alert - {product_count} Products",
                body_template="""Low Stock Alert - {alert_date}

The following {product_count} products are running low on inventory:

{product_list}

Please review and restock as needed.
Dashboard: {dashboard_url}""",
                variables=['alert_date', 'product_count', 'product_list', 'dashboard_url']
            ),
            
            NotificationTemplate(
                template_id="order_shipped_email",
                notification_type=NotificationType.ORDER_SHIPPED,
                channel=NotificationChannel.EMAIL,
                subject_template="Order Shipped - #{order_id}",
                body_template="""Your order has been shipped!

Order Details:
- Order ID: {order_id}
- Tracking ID: {tracking_id}
- Shipping Date: {shipping_date}
- Carrier: {carrier}
- Estimated Delivery: {estimated_delivery}

You can track your package using the tracking ID above.

Thank you for your business!""",
                variables=['order_id', 'tracking_id', 'shipping_date', 'carrier', 'estimated_delivery']
            )
        ]
        
        for template in default_templates:
            try:
                self.notification_repo.save_template(template)
            except Exception as e:
                logger.error(f"Failed to save default template: {e}")
    
    def shutdown(self) -> None:
        """Shutdown notification service"""
        self.stop_processing.set()
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics for monitoring"""
        return {
            'service': 'NotificationService',
            'channels_registered': len(self.channels),
            'queue_size': self.notification_queue.qsize(),
            'processing_enabled': self.processing_enabled,
            'background_thread_alive': self.processing_thread.is_alive() if self.processing_thread else False
        }
