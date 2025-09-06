import logging
from core.entities.notification import Notification, NotificationChannelType
from core.interfaces.notification_sender import NotificationSender

logger = logging.getLogger(__name__)

class PushSender(NotificationSender):
    """Email notification sender implementation"""

    def __init__(self):
        pass

    def send(self, notification: Notification) -> bool:
        try:
            # Get recipient email
            recipient_device_id = notification.dest.device_id
            subject = f"Notification: {notification.message.type.name}"
            body = notification.get_formatted_message({})

            # Simulate email sending (in real world: SendGrid, SES, etc.)
            logger.info(f"Sending email to {recipient_device_id}")
            logger.info(f"Subject: {subject}, Body: {body}")


            logger.info(f"Email sent successfully to {recipient_device_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    def get_channel_type(self) -> str:
        return NotificationChannelType.PUSH.name