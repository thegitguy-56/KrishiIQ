import time

from utils.logger import get_logger
from utils.retry import retry, is_connection_error
from utils.flutter_helpers import text_visible, key_visible

log = get_logger(__name__)

# appium-flutter-driver has no concept of a URL/route string (that's a
# go_router-internal detail, never exposed to the widget tree or any
# Appium command). current_route_contains() therefore checks for a
# screen-specific visible-text marker instead, mapped from the fragment
# names used throughout the suite.
_ROUTE_TEXT_MARKERS = {
    "main": "Quick Actions",
    "mainshell": "Quick Actions",
    "farm-setup": "Land Area",
    "login": "Phone Number",
    "register": "Full Name",
}


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

    def by_type(self, widget_type: str):
        from appium_flutter_finder import FlutterElement

        return FlutterElement(self.driver, self.finder.by_type(widget_type))

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

    @retry(times=2, delay=1)
    def get_text(self, element) -> str:
        return element.text

    def wait(self, seconds: float = 1.0):
        time.sleep(seconds)

    def is_present(self, element, timeout: int = 5) -> bool:
        """Uses is_displayed(), not .text — see utils/flutter_helpers.key_visible
        for why: .text (getText) only resolves for Text/EditableText widgets,
        and this helper is used generically on arbitrary elements, many of
        which have no text at all."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if element.is_displayed():
                    return True
            except Exception as exc:  # noqa: BLE001
                if is_connection_error(exc) and hasattr(self.driver, "recreate"):
                    log.warning("Connection error in is_present, recreating session...")
                    self.driver.recreate()
            time.sleep(0.5)
        return False

    def is_text_present(self, text: str, timeout: float = 5) -> bool:
        return text_visible(self.driver, self.finder, text, timeout)

    def is_key_present(self, value_key: str, timeout: float = 5) -> bool:
        return key_visible(self.driver, self.finder, value_key, timeout)

    def current_route_contains(self, fragment: str) -> bool:
        """Best-effort screen check via a visible-text marker (see
        _ROUTE_TEXT_MARKERS). appium-flutter-driver has no route/URL
        concept and no getPageSource, so an exact route match isn't
        possible — this checks for text that's unique to the target
        screen instead."""
        marker = _ROUTE_TEXT_MARKERS.get(fragment.lower(), fragment)
        return self.is_text_present(marker, timeout=4)

    def take_screenshot(self, name: str):
        from config.settings import settings
        import os

        path = os.path.join(settings.SCREENSHOTS_DIR, f"{name}.png")
        self.driver.get_screenshot_as_file(path)
        return path