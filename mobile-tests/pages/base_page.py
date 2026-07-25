import time

from utils.logger import get_logger
from utils.retry import retry

log = get_logger(__name__)


class BasePage:
    """Common Page Object helpers shared by every screen. All finder calls
    go through appium-flutter-driver's FlutterElement, which talks to the
    app's widget tree directly (fast + resilient to layout changes)."""

    def __init__(self, driver, finder):
        self.driver = driver
        self.finder = finder

    # -- low level ---------------------------------------------------------
    def by_key(self, key: str):
        from appium_flutter_finder import FlutterElement

        return FlutterElement(self.driver, self.finder.by_value_key(key))

    def by_text(self, text: str):
        from appium_flutter_finder import FlutterElement

        return FlutterElement(self.driver, self.finder.by_text(text))

    def by_tooltip(self, message: str):
        from appium_flutter_finder import FlutterElement

        return FlutterElement(self.driver, self.finder.by_tooltip(message))

    # -- actions (retry-wrapped for flaky-widget-tree timing) --------------
    @retry(times=2, delay=1)
    def tap(self, element):
        element.click()

    @retry(times=2, delay=1)
    def type_text(self, element, text: str, clear_first: bool = True):
        if clear_first:
            try:
                element.clear()
            except Exception:  # noqa: BLE001
                pass
        element.send_keys(text)

    def get_text(self, element) -> str:
        return element.text

    def wait(self, seconds: float = 1.0):
        time.sleep(seconds)

    def is_present(self, element, timeout: int = 5) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                element.text  # touching the element proves it resolves
                return True
            except Exception:  # noqa: BLE001
                time.sleep(0.5)
        return False

    def current_route_contains(self, fragment: str) -> bool:
        """Best-effort route check via page_source (go_router exposes the
        route name in the widget tree for debug builds)."""
        try:
            return fragment in self.driver.page_source
        except Exception:  # noqa: BLE001
            return False

    def take_screenshot(self, name: str):
        from config.settings import settings
        import os

        path = os.path.join(settings.SCREENSHOTS_DIR, f"{name}.png")
        self.driver.get_screenshot_as_file(path)
        return path
