import base64
import os
import socket
import time
import json

import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium_flutter_finder.flutter_finder import FlutterFinder

from config.capabilities import build_capabilities
from config.settings import settings
from utils.logger import get_logger

log = get_logger(__name__)

os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(settings.LOGS_DIR, exist_ok=True)

# Process-wide default: bounds every socket (including the ones Selenium/
# Appium's HTTP client opens under the hood) that doesn't set its own
# timeout. Without this, a wedged FlutterDriver/Observatory command blocks
# forever with no error at all — see APPIUM_COMMAND_TIMEOUT in
# config/settings.py for the full reasoning.
socket.setdefaulttimeout(settings.APPIUM_COMMAND_TIMEOUT)


class ResilientDriver:
    """Wraps a live Appium session so it can be transparently recreated if
    it becomes unresponsive, without every test/fixture needing to know
    the session was swapped out. All test code keeps calling driver.foo(...)
    exactly as before; unrecognized attributes are forwarded to whichever
    real session is currently live.
    """

    def __init__(self):
        self._raw = None
        self._create()

    def _create(self):
        caps = build_capabilities()
        options = UiAutomator2Options().load_capabilities(caps)
        self._raw = webdriver.Remote(settings.APPIUM_SERVER_URL, options=options)
        self._raw.implicitly_wait(settings.IMPLICIT_WAIT)
        log.info("Appium session started: %s", self._raw.session_id)

    def is_healthy(self):
        """Cheap native-Android call (handled directly by UiAutomator2)
        that never touches the Flutter/Observatory channel, so it isn't
        subject to the hang we've seen wedge FlutterDriver commands.
        Bounded by the global socket timeout set above."""
        try:
            self._raw.get_window_size()
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("Driver health check failed, session looks wedged: %s", exc)
            return False

    def recreate(self):
        log.warning("Recreating Appium session %s", getattr(self._raw, "session_id", "?"))
        try:
            self._raw.quit()
        except Exception as exc:  # noqa: BLE001
            log.warning("Quit on wedged session raised (ignoring): %s", exc)
        self._create()

    def __getattr__(self, name):
        # Forwards everything else — terminate_app, activate_app,
        # find_element, execute_script, get_screenshot_as_file,
        # get_log, page_source, quit, etc. — to the live session.
        return getattr(self._raw, name)


# --------------------------------------------------------------------------- #
# Appium session — one driver per test-worker (pytest-xdist safe), reused
# across tests in that worker for speed. Health-checked and transparently
# recreated between tests if the underlying session has wedged, so one
# stuck command can no longer take down every remaining test in the shard.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def driver():
    d = ResilientDriver()
    yield d
    try:
        d.quit()
    except Exception as exc:  # noqa: BLE001
        log.warning("Driver quit raised: %s", exc)


@pytest.fixture(scope="session")
def finder():
    return FlutterFinder()


@pytest.fixture(autouse=True)
def _restart_app_between_tests(driver, request):
    """Relaunch the app fresh before every test so state never leaks
    between the 400+ parametrized cases (fast: activity restart, not a
    full emulator/app reinstall)."""
    if not driver.is_healthy():
        driver.recreate()
    try:
        driver.terminate_app(settings.APP_PACKAGE)
    except Exception:  # noqa: BLE001
        pass
    driver.activate_app(settings.APP_PACKAGE)
    time.sleep(1.5)
    yield


# --------------------------------------------------------------------------- #
# Failure capture: screenshot + Appium/device logs, named after the test id
# --------------------------------------------------------------------------- #
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when == "call" and report.failed:
        driver = item.funcargs.get("driver")
        if driver is None:
            return
        safe_name = item.nodeid.replace("/", "_").replace("::", "__")

        # Screenshot
        try:
            shot_path = os.path.join(settings.SCREENSHOTS_DIR, f"{safe_name}.png")
            driver.get_screenshot_as_file(shot_path)
            log.info("Saved failure screenshot: %s", shot_path)
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not capture screenshot for %s: %s", item.nodeid, exc)

        # Device / logcat logs
        try:
            logs = driver.get_log("logcat")
            log_path = os.path.join(settings.LOGS_DIR, f"{safe_name}.log")
            with open(log_path, "w", encoding="utf-8") as fh:
                for entry in logs[-500:]:
                    fh.write(f"{entry.get('timestamp')} {entry.get('message')}\n")
            log.info("Saved device log: %s", log_path)
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not capture logcat for %s: %s", item.nodeid, exc)

        # Appium server-side session log (page source at time of failure)
        try:
            src_path = os.path.join(settings.LOGS_DIR, f"{safe_name}.page_source.xml")
            with open(src_path, "w", encoding="utf-8") as fh:
                fh.write(driver.page_source)
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not capture page source for %s: %s", item.nodeid, exc)


def pytest_sessionfinish(session, exitstatus):
    """Write a small machine-readable run summary used by report_generator.py"""
    summary = {
        "exit_status": exitstatus,
        "reports_dir": settings.REPORTS_DIR,
    }
    with open(os.path.join(settings.REPORTS_DIR, "run_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)