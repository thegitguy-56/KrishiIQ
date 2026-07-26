import os
import time
import json

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

# Client-side HTTP timeout for every Appium/Selenium request. This is the
# actual, cheap defensive measure: if a command ever wedges (shouldn't
# happen now that the backend is started before tests run — see
# android-e2e.yml — but kept as a safety net for genuine one-off hiccups),
# it fails after this many seconds instead of hanging forever. It does
# NOT recreate the session — a single failed/timed-out command should
# just fail that one test (pytest-rerunfailures already retries it), not
# cost a fresh ~25-30s session bootstrap. A prior version of this file
# added a per-test health-check-and-recreate wrapper that fired on nearly
# every test (21-79 recreations per 101-test shard, observed directly in
# CI logs) and was overwhelmingly the largest cost in the whole run —
# removed for that reason.
AppiumConnection.set_timeout(settings.APPIUM_COMMAND_TIMEOUT)


# --------------------------------------------------------------------------- #
# Appium session — one per shard's pytest process, reused across every test
# in that shard for speed. No per-test health check / recreate: a command
# that times out fails that one test cleanly (and gets rerun by
# pytest-rerunfailures) rather than tearing down and rebuilding the whole
# session.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def driver():
    caps = build_capabilities()
    options = UiAutomator2Options().load_capabilities(caps)
    session = webdriver.Remote(settings.APPIUM_SERVER_URL, options=options)
    session.implicitly_wait(settings.IMPLICIT_WAIT)
    log.info("Appium session started: %s", session.session_id)
    yield session
    try:
        session.quit()
    except Exception as exc:  # noqa: BLE001
        log.warning("Driver quit raised: %s", exc)


@pytest.fixture(scope="session")
def finder():
    return FlutterFinder()


@pytest.fixture(autouse=True)
def _restart_app_between_tests(driver, request):
    """Relaunch the app fresh before every test so state never leaks
    between the 400+ parametrized cases (fast: activity restart, not a
    full emulator/app reinstall or session recreate)."""
    try:
        driver.terminate_app(settings.APP_PACKAGE)
    except Exception:  # noqa: BLE001
        pass
    driver.activate_app(settings.APP_PACKAGE)
    yield


# --------------------------------------------------------------------------- #
# Failure capture: screenshot + device logs, named after the test id.
# Page source is deliberately NOT captured here — appium-flutter-driver
# doesn't implement getPageSource (permanent 405), so calling it on every
# failure was pure wasted time with an always-empty result.
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

        try:
            shot_path = os.path.join(settings.SCREENSHOTS_DIR, f"{safe_name}.png")
            driver.get_screenshot_as_file(shot_path)
            log.info("Saved failure screenshot: %s", shot_path)
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not capture screenshot for %s: %s", item.nodeid, exc)

        try:
            logs = driver.get_log("logcat")
            log_path = os.path.join(settings.LOGS_DIR, f"{safe_name}.log")
            with open(log_path, "w", encoding="utf-8") as fh:
                for entry in logs[-500:]:
                    fh.write(f"{entry.get('timestamp')} {entry.get('message')}\n")
            log.info("Saved device log: %s", log_path)
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not capture logcat for %s: %s", item.nodeid, exc)


def pytest_sessionfinish(session, exitstatus):
    """Write a small machine-readable run summary used by report_generator.py"""
    summary = {
        "exit_status": exitstatus,
        "reports_dir": settings.REPORTS_DIR,
    }
    with open(os.path.join(settings.REPORTS_DIR, "run_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
