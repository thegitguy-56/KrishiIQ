"""
appium-flutter-driver does NOT implement getPageSource (GET .../source
returns 405 NotYetImplementedError) — that's documented, permanent
behavior of this driver, since it drives the app over the Dart VM Service
protocol rather than dumping a UiAutomator2-style view-tree XML.

text_visible() is the supported replacement used everywhere the suite
used to do `"X" in driver.page_source`: it resolves a byText finder
(the same mechanism already used successfully for taps throughout this
suite) instead of dumping/parsing page source.
"""
import time

from appium_flutter_finder import FlutterElement


def text_visible(driver, finder, text: str, timeout: float = 5) -> bool:
    element = FlutterElement(driver, finder.by_text(text))
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            _ = element.text
            return True
        except Exception:  # noqa: BLE001
            time.sleep(0.4)
    return False


def key_visible(driver, finder, value_key: str, timeout: float = 5) -> bool:
    """Note: uses is_displayed(), not .text. .text calls the Flutter
    driver's getText command, which only resolves for Text/EditableText
    widgets or their descendants. key_visible is used on plenty of
    non-text widgets too (e.g. HomePage.NOTIFICATIONS_BUTTON, an
    IconButton with no text anywhere in its subtree) — for those,
    .text raised on every single poll for the full timeout, not just on
    genuine visibility delays, which made every key_visible(...) check
    against a non-text widget fail unconditionally. is_displayed() works
    for any widget type and is the correct existence+visibility check
    regardless of what's inside it."""
    element = FlutterElement(driver, finder.by_value_key(value_key))
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if element.is_displayed():
                return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.4)
    return False