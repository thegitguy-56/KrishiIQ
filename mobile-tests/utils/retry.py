import functools
import time

from utils.logger import get_logger

log = get_logger(__name__)


def retry(times: int = 2, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """Retries a flaky UI action (e.g. widget not yet attached to the tree)
    before letting the exception propagate to pytest-rerunfailures, which
    handles the higher-level 'retry the whole test' story."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, times + 2):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:  # noqa: BLE001
                    last_exc = exc
                    log.warning(
                        "%s attempt %d/%d failed: %s",
                        func.__name__,
                        attempt,
                        times + 1,
                        exc,
                    )
                    if attempt <= times:
                        time.sleep(delay)
            raise last_exc

        return wrapper

    return decorator
