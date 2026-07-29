"""
Device-level actions (backgrounding the app, toggling connectivity) driven
straight through adb instead of through the Appium session.

Why this exists: driver.background_app(seconds) maps to the Appium
extension command "mobile: backgroundApp", and driver.set_network_connection()
maps to "setNetworkConnection" / "mobile: networkConnection". Both are
UiAutomator2/Espresso automation-engine commands. This suite runs with
automationName=Flutter (config/capabilities.py) so it can use FlutterFinder
widget-level finders — and the Flutter automation engine does not implement
either extension. Every call raised:
    "Command not supported: mobile: backgroundApp"
(see conftest fixture history / execution-results.json,
tests/test_session_management.py, tests/test_offline_handling.py).

adb runs alongside the Appium server in CI (android-e2e.yml boots the
emulator with the standard Android SDK tools on PATH), so we drive these
two device-level actions directly instead of going through the Flutter
driver at all.
"""

import re
import subprocess
import time

from config.settings import settings
from utils.logger import get_logger

log = get_logger(__name__)

_ADB = ["adb", "-s", settings.DEVICE_NAME]


def _run(*args: str, timeout: int = 15) -> subprocess.CompletedProcess:
    cmd = [*_ADB, *args]
    log.info("adb: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def background_app(seconds: float = 2.0) -> None:
    """Send the app to the background (HOME key) and bring it back to the
    foreground after `seconds`, mirroring the old
    driver.background_app(seconds) call site-for-site."""
    result = _run("shell", "input", "keyevent", "KEYCODE_HOME")
    if result.returncode != 0:
        log.warning("adb HOME keyevent failed: %s", result.stderr.strip())

    time.sleep(seconds)

    result = _run(
        "shell", "monkey",
        "-p", settings.APP_PACKAGE,
        "-c", "android.intent.category.LAUNCHER", "1",
    )
    if result.returncode != 0:
        log.warning("adb foreground relaunch failed: %s", result.stderr.strip())
    # Give the activity a beat to actually redraw before the next assertion.
    time.sleep(1)


def scroll_down(percent: float = 0.6) -> None:
    """Scroll the screen down via a raw adb swipe.

    driver.execute_script("mobile: scrollGesture", {...}) maps to the same
    UiAutomator2/Espresso automation-engine command family as
    backgroundApp/networkConnection above, and fails the exact same way
    under automationName=Flutter: every call returned HTTP 500
    ("Command not supported: mobile: scrollGesture") in 1ms, in
    appium-server_-_1_latest.log (5x, tests/test_advisory_profile.py) and
    appium-server-_4_latest.log (1x, pages/home_page.py:pull_to_refresh).
    It was already wrapped in a bare `except: pass` at both call sites, so
    it never crashed anything — it just silently did nothing, making
    test_dashboard_pull_to_refresh and test_advisory_feed_scroll_stability
    vacuously pass without ever actually scrolling.

    `percent` mirrors the old scrollGesture "percent" arg: fraction of the
    screen height to swipe through, starting 3/4 of the way down.
    """
    size_result = _run("shell", "wm", "size")
    match = re.search(r"(\d+)x(\d+)", size_result.stdout)
    if size_result.returncode != 0 or not match:
        raise RuntimeError(
            f"adb shell wm size failed (rc={size_result.returncode}): "
            f"{(size_result.stderr or size_result.stdout).strip()}"
        )
    width, height = int(match.group(1)), int(match.group(2))
    x = width // 2
    y_start = int(height * 0.75)
    y_end = max(int(y_start - height * percent), int(height * 0.1))

    result = _run("shell", "input", "swipe", str(x), str(y_start), str(x), str(y_end), "200")
    if result.returncode != 0:
        raise RuntimeError(
            f"adb shell input swipe failed (rc={result.returncode}): {result.stderr.strip()}"
        )
    # Let the scroll/refresh animation settle before the next assertion.
    time.sleep(0.5)


def set_network_enabled(enabled: bool) -> None:
    """Toggle both wifi and mobile data. Raises if adb itself is
    unreachable (misconfigured device/CI) rather than silently no-op'ing,
    so a broken environment shows up as a real failure instead of every
    offline test quietly skipping the way it did before."""
    state = "enable" if enabled else "disable"
    for radio in ("wifi", "data"):
        result = _run("shell", "svc", radio, state)
        if result.returncode != 0:
            raise RuntimeError(
                f"adb shell svc {radio} {state} failed (rc={result.returncode}): "
                f"{result.stderr.strip()}"
            )
    # Let connectivity state actually settle before the test proceeds.
    time.sleep(2)