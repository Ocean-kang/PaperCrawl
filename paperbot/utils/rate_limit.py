import time
import threading
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, calls_per_second: float = 2.0) -> None:
        self.min_interval = 1.0 / calls_per_second
        self._last_call: float = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self._last_call = time.monotonic()
