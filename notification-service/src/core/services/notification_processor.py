import time
import logging
from datetime import datetime
from core.entities.notification import Notification, NotificationStatus
from core.interfaces.notification_sender import NotificationSender
from core.interfaces.repositories.notification_repository import NotificationRepository


class NotificationProcessor:
    """Handles notification processing with retry logic and exponential backoff"""

    def __init__(self, notification_repository: NotificationRepository):
        self.notification_repository = notification_repository
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3
        self.base_delay = 1  # Base delay in seconds

    def process_notification(self, notification: Notification, sender: NotificationSender) -> bool:
        """
        Process a notification with retry logic

        Args:
            notification: The notification to process
            sender: The notification sender to use

        Returns:
            bool: True if successfully sent, False if failed after all retries
        """
        retry_count = 0

        while retry_count <= self.max_retries:
            try:
                # Update notification retry info
                notification.retry_count = retry_count
                notification.last_retry_at = datetime.now()

                if retry_count > 0:
                    notification.status = NotificationStatus.PENDING
                    self.logger.info(f"Retrying notification {notification.id}, attempt {retry_count}")

                # Attempt to send the notification
                success = sender.send(notification)

                if success:
                    notification.status = NotificationStatus.SENT
                    notification.sent_at = datetime.now()
                    self.notification_repository.save(notification)
                    self.logger.info(f"Notification {notification.id} sent successfully")
                    return True
                else:
                    # Send failed, prepare for retry
                    notification.status = NotificationStatus.FAILED
                    self.notification_repository.save(notification)

                    if retry_count < self.max_retries:
                        # Calculate exponential backoff delay
                        delay = self.base_delay * (2 ** retry_count)
                        self.logger.warning(f"Notification {notification.id} failed, retrying in {delay} seconds")
                        time.sleep(delay)
                    else:
                        self.logger.error(f"Notification {notification.id} failed after {self.max_retries} retries")
                        return False

            except Exception as e:
                self.logger.error(f"Error processing notification {notification.id}: {str(e)}")
                notification.status = NotificationStatus.FAILED
                self.notification_repository.save(notification)

                if retry_count < self.max_retries:
                    delay = self.base_delay * (2 ** retry_count)
                    self.logger.warning(f"Retrying notification {notification.id} in {delay} seconds due to error")
                    time.sleep(delay)
                else:
                    return False

            retry_count += 1

        return False

    def should_retry(self, notification: Notification) -> bool:
        """Check if a notification should be retried"""
        if notification.status != NotificationStatus.FAILED:
            return False

        if notification.retry_count >= self.max_retries:
            return False

        # Check if enough time has passed since last retry
        if notification.last_retry_at:
            min_retry_interval = self.base_delay * (2 ** notification.retry_count)
            time_since_retry = (datetime.now() - notification.last_retry_at).total_seconds()
            return time_since_retry >= min_retry_interval

        return True