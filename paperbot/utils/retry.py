import logging
from functools import wraps
from typing import Any, Callable

import requests

logger = logging.getLogger(__name__)


def is_retryable(exception: Exception) -> bool:
    if isinstance(exception, requests.Timeout):
        return True
    if isinstance(exception, requests.ConnectionError):
        return True
    if isinstance(exception, requests.HTTPError):
        status = exception.response.status_code if exception.response is not None else 0
        return status in (429, 502, 503, 504)
    return False
