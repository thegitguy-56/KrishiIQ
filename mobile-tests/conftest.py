import os
import signal
import time
import json

import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.client_config import AppiumClientConfig
from appium_flutter_finder.flutter_finder import FlutterFinder

from config.capabilities import build_capabilities
from config.settings import settings
from utils.logger import get_logger

log = get_logger(__name__)

os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(settings.LOGS_DIR, exist_ok=True)

# Client-side HTTP timeout for every Appium/Selenium request. This is the
# actual, cheap defensive measure: if a command ever wedges (shouldn't
# happen now that the backend is started before tests run — see
# android-e2e.yml — but kept as a safety net for genuine one-off hiccups),
# it fails after this many seconds instead of hanging forever.
#
# NOTE: this used to be `AppiumConnection.set_timeout(...)`, called once
# at import time. That silently did nothing: RemoteConnection.__init__
# builds a brand-new ClientConfig (default timeout = socket.getdefaulttimeout(),
# i.e. None/blocking) every time webdriver.Remote() constructs a session,
# and overwrites the class attribute set_timeout() had just set — see
# selenium/webdriver/remote/remote_connection.py, the
# "RemoteConnection._client_config = self._client_config" line in
# __init__ (selenium/selenium#14694). Net effect: there was NO client-side
# timeout at all, so a wedged Appium call blocked until pytest-timeout's
# 180s alarm fired at the raw socket level instead — confirmed directly
# via `Failed: Timeout >180.0s` at socket.py:718 in test failures. The fix
# is to build the ClientConfig ourselves and hand it to webdriver.Remote()
# explicitly (see _create() below), which is the only way it actually
# takes effect now.
_CLIENT_CONFIG = AppiumClientConfig(
    remote_server_addr=settings.APPIUM_SERVER_URL,
    timeout=settings.APPIUM_COMMAND_TIMEOUT,
)


# --------------------------------------------------------------------------- #
# Appium session — one per shard's pytest process, reused across every test
# in that shard for speed. No proactive per-test health check (that version
# fired 21-79 times per 101-test shard and was the dominant cost). Instead,
# recovery is purely reactive: if relaunching the app before a test fails
# (observed cause: the Flutter Observatory connection drops and
# FlutterDriver can never reconnect it again for the rest of that session —
# "No matched log found" in appium-server.log — which previously ERRORed
# every single remaining test in the shard with no recovery), we quit the
# dead session and open a fresh one, once, right then.
# --------------------------------------------------------------------------- #
class ResilientDriver:
    def __init__(self):
        self._raw = None
        self._create()

    def _create(self):
        caps = build_capabilities()
        options = UiAutomator2Options().load_capabilities(caps)
        self._raw = webdriver.Remote(settings.APPIUM_SERVER_URL, options=options, client_config=_CLIENT_CONFIG)
        self._raw.implicitly_wait(settings.IMPLICIT_WAIT)
        log.info("Appium session started: %s", self._raw.session_id)

    def recreate(self):
        log.warning(
            "Recreating Appium session %s (activate_app failed, looks dead)",
            getattr(self._raw, "session_id", "?"),
        )
        try:
            self._raw.quit()
        except Exception as exc:  # noqa: BLE001
            log.warning("Quit on dead session raised (ignoring): %s", exc)
        self._create()

    def __getattr__(self, name):
        # Forwards everything else — terminate_app, activate_app,
        # find_element, execute_script, get_screenshot_as_file, get_log,
        # quit, etc. — to whichever real session is currently live.
        return getattr(self._raw, name)


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
    full emulator/app reinstall). If the relaunch itself fails, the
    session has gone bad (see class docstring above) — recreate it once
    and retry the relaunch on the fresh session rather than ERRORing
    every remaining test in the shard."""
    try:
        driver.terminate_app(settings.APP_PACKAGE)
    except Exception:  # noqa: BLE001
        pass
    try:
        driver.activate_app(settings.APP_PACKAGE)
    except Exception as exc:  # noqa: BLE001
        log.warning("activate_app failed (%s) — recreating session", exc)
        driver.recreate()
        driver.activate_app(settings.APP_PACKAGE)
    yield


# --------------------------------------------------------------------------- #
# Failure capture: screenshot + device logs, named after the test id.
# Page source is deliberately NOT captured here — appium-flutter-driver
# doesn't implement getPageSource (permanent 405), so calling it on every
# failure was pure wasted time with an always-empty result.
#
# IMPORTANT: pytest-timeout's alarm (method="signal") is armed for the
# *whole* test item, including this makereport hook that runs right after
# a failed call. If the driver is already unresponsive (frequently why the
# test failed in the first place), the 180s alarm can fire WHILE we're
# blocked inside get_screenshot_as_file()/get_log(). When it fires, the
# signal handler raises _pytest.outcomes.Failed, which subclasses
# BaseException (not Exception) — by design, so pytest's own internals
# never accidentally swallow it. That meant our `except Exception` here
# never caught it: it propagated straight out of this hookwrapper and
# crashed the whole session with INTERNALERROR, silently skipping every
# remaining test in the shard. Fix: disarm the pending alarm before doing
# any cleanup I/O, and catch BaseException (not just Exception) around
# each capture step so nothing here can ever take down the session.
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

        # Disarm any pending pytest-timeout SIGALRM so it can't fire in the
        # middle of the screenshot/logcat HTTP calls below and crash the
        # session with INTERNALERROR. Safe no-op if no alarm is pending or
        # on platforms without SIGALRM (e.g. Windows).
        try:
            signal.alarm(0)
        except (AttributeError, ValueError):  # noqa: BLE001
            pass

        try:
            shot_path = os.path.join(settings.SCREENSHOTS_DIR, f"{safe_name}.png")
            driver.get_screenshot_as_file(shot_path)
            log.info("Saved failure screenshot: %s", shot_path)
        except BaseException as exc:  # noqa: BLE001
            log.warning("Could not capture screenshot for %s: %s", item.nodeid, exc)

        try:
            logs = driver.get_log("logcat")
            log_path = os.path.join(settings.LOGS_DIR, f"{safe_name}.log")
            with open(log_path, "w", encoding="utf-8") as fh:
                for entry in logs[-500:]:
                    fh.write(f"{entry.get('timestamp')} {entry.get('message')}\n")
            log.info("Saved device log: %s", log_path)
        except BaseException as exc:  # noqa: BLE001
            log.warning("Could not capture logcat for %s: %s", item.nodeid, exc)


def pytest_sessionfinish(session, exitstatus):
    """Write a small machine-readable run summary used by report_generator.py"""
    summary = {
        "exit_status": exitstatus,
        "reports_dir": settings.REPORTS_DIR,
    }
    with open(os.path.join(settings.REPORTS_DIR, "run_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)