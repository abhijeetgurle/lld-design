import time
from collections import defaultdict, deque
from typing import Dict, Deque
import threading


class RateLimiter:
    """Rate limiter implementation using sliding window approach"""

    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum number of requests allowed (default: 10)
            time_window: Time window in seconds (default: 60 = 1 minute)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self._user_requests: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def can_send(self, user_id: str) -> bool:
        """
        Check if user can send a notification based on rate limiting

        Args:
            user_id: The user ID to check

        Returns:
            bool: True if user can send, False if rate limited
        """
        with self._lock:
            current_time = time.time()
            user_requests = self._user_requests[user_id]

            # Remove old requests outside the time window
            while user_requests and current_time - user_requests[0] > self.time_window:
                user_requests.popleft()

            # Check if user has exceeded the limit
            if len(user_requests) >= self.max_requests:
                return False

            # Add current request timestamp
            user_requests.append(current_time)
            return True

    def get_remaining_requests(self, user_id: str) -> int:
        """Get remaining requests for a user in current time window"""
        with self._lock:
            current_time = time.time()
            user_requests = self._user_requests[user_id]

            # Remove old requests
            while user_requests and current_time - user_requests[0] > self.time_window:
                user_requests.popleft()

            return max(0, self.max_requests - len(user_requests))

    def get_reset_time(self, user_id: str) -> float:
        """Get time when rate limit will reset for a user"""
        with self._lock:
            user_requests = self._user_requests[user_id]

            if not user_requests or len(user_requests) < self.max_requests:
                return 0

            return user_requests[0] + self.time_window

    def clear_user_history(self, user_id: str):
        """Clear rate limiting history for a user (useful for testing)"""
        with self._lock:
            if user_id in self._user_requests:
                del self._user_requests[user_id]