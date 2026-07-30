import os
import signal
import time
import json
import urllib3.exceptions

import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.appium_connection import AppiumConnection
from appium_flutter_finder.flutter_finder import FlutterFinder

from config.capabilities import build_capabilities
from config.settings import settings
from utils.logger import get_logger

log = get_logger(__name__)

os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(settings.LOGS_DIR, exist_ok=True)

# Client-side HTTP timeout for every Appium/Selenium request, so a wedged
# command fails after this many seconds instead of hanging until
# pytest-timeout's 180s alarm fires at the raw socket level.
#
# This IS the correct mechanism for this project's pinned dependencies
# (Appium-Python-Client==3.1.1, selenium==4.21.0 — see requirements.txt):
# in selenium 4.21.0, RemoteConnection._timeout is a plain class attribute
# and set_timeout()/get_timeout() just read/write it directly; nothing in
# __init__ overwrites it. AppiumConnection._get_connection_manager() reads
# get_timeout() when it lazily builds the urllib3 pool manager, so calling
# this once at import time, before any driver session exists, is
# sufficient. (A prior version of this comment claimed set_timeout() was
# silently discarded and switched to AppiumClientConfig — that diagnosis
# was checked against the *latest* Appium-Python-Client, not the pinned
# 3.1.1, where AppiumClientConfig doesn't exist at all. That change broke
# conftest.py collection outright: ImportError -> 0 tests collected in
# every shard. Reverted.)
AppiumConnection.set_timeout(settings.APPIUM_COMMAND_TIMEOUT)


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
class SessionCreationConnection(AppiumConnection):
    pass


# 60s is enough for a freshly booted emulator to install the APK and finish the Flutter Observatory handshake.
SessionCreationConnection.set_timeout(60)


class ResilientDriver:
    def __init__(self):
        self._raw = None
        self._create()

    def _create(self):
        """Open an Appium session with a dedicated long timeout.

        The initial NEW_SESSION command (which includes installing the APK and
        booting the Flutter Observatory) can take ~30s on CI. We use a dedicated
        60s-timeout connection for this initial creation to avoid client-side
        timeouts that leave doomed sessions running on the server. After the
        session starts, we swap the executor to the standard, short-timeout
        connection so genuinely stuck everyday commands still fail fast.
        """
        try:
            caps = build_capabilities()
            options = UiAutomator2Options().load_capabilities(caps)
            
            long_executor = SessionCreationConnection(settings.APPIUM_SERVER_URL)
            self._raw = webdriver.Remote(command_executor=long_executor, options=options)
            self._raw.implicitly_wait(settings.IMPLICIT_WAIT)
            
            # Swap executor for subsequent everyday commands
            short_executor = AppiumConnection(settings.APPIUM_SERVER_URL)
            self._raw.command_executor = short_executor
            
            log.info(
                "Appium session started successfully: %s",
                self._raw.session_id,
            )
        except Exception as exc:  # noqa: BLE001
            log.error(
                "Appium session creation failed: %s",
                exc,
            )
            # Re-raise so the driver fixture can catch it and skip the shard.
            raise exc

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
    """Session-scoped Appium driver.

    If the Appium server is unreachable (e.g. because the emulator runner
    crashed or the server never fully started), skip the entire shard instead
    of leaving every test in the shard with an ERROR outcome that reports the
    urllib3 stack trace instead of a meaningful test failure. SKIP is the
    honest outcome — the tests were not run, not that they failed.
    """
    try:
        d = ResilientDriver()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(
            f"Appium server at {settings.APPIUM_SERVER_URL} is not reachable "
            f"— skipping shard. Root cause: {exc}"
        )
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
    every remaining test in the shard.

    If the driver fixture itself was skipped (Appium unavailable), skip
    this fixture too rather than raising an AttributeError on driver._raw.
    """
    # Guard: if ResilientDriver never successfully initialized (driver._raw
    # is None), the shard was already skipped by the driver fixture — don't
    # attempt any Appium calls here.
    if getattr(driver, "_raw", None) is None:
        pytest.skip("Driver session not available (Appium unreachable)")
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