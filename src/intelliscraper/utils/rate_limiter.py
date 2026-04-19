import time
from collections import deque
from typing import Deque
from intelliscraper.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    def __init__(self, max_requests: int = 5, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests: Deque[float] = deque()

    def wait_if_needed(self) -> None:
        now = time.time()
        self.requests = deque(t for t in self.requests if now - t < self.window)

        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return

        sleep_time = self.window - (now - self.requests[0]) + 0.1
        if sleep_time > 0:
            logger.info(f"Rate limit reached. Sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.requests.clear()
        self.requests.append(time.time())

    def reset(self) -> None:
        self.requests.clear()


rate_limiter = RateLimiter()
