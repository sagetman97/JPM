"""
Rate limiter utility for API calls.
"""

import time
import threading
from typing import Dict, Optional
from config.settings import settings

class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
        self.lock = threading.Lock()
        self.min_interval = window_seconds / max_requests  # Minimum time between requests
    
    def can_make_request(self) -> bool:
        """Check if we can make a request without exceeding rate limits."""
        with self.lock:
            now = time.time()
            # Remove old requests outside the window
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.window_seconds]
            
            # Check if we're under the limit
            return len(self.requests) < self.max_requests
    
    def record_request(self):
        """Record that a request was made."""
        with self.lock:
            self.requests.append(time.time())
    
    def wait_if_needed(self, max_wait: int = 30):
        """Wait if we need to respect rate limits."""
        with self.lock:
            now = time.time()
            # Remove old requests outside the window
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.window_seconds]
            
            # If we're at the limit, wait
            if len(self.requests) >= self.max_requests:
                # Wait until the oldest request expires
                oldest_request = min(self.requests)
                wait_time = self.window_seconds - (now - oldest_request) + 1
                if wait_time > 0 and wait_time <= max_wait:
                    time.sleep(wait_time)
                elif wait_time > max_wait:
                    raise Exception("Rate limit exceeded, waited too long")
            
            # Record this request
            self.requests.append(time.time())

# Global rate limiter instance
api_rate_limiter = RateLimiter(
    max_requests=settings.MAX_REQUESTS_PER_MINUTE,
    window_seconds=60
) 