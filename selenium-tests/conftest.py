"""
conftest.py — pytest fixtures shared across all test modules.
"""
import logging
import os
import json
import time
from datetime import datetime
from typing import Generator

import pytest

import config
from driver_factory import create_driver
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.farmers_page import FarmersPage
from pages.disease_alerts_page import DiseaseAlertsPage
from pages.other_pages import AnalyticsPage, MapPage, UnauthorizedPage

# ── Ensure report directories exist ───────────────────────────────────────────
os.makedirs(config.SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(config.LOGS_DIR, exist_ok=True)
os.makedirs(config.REPORTS_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

# ── Global test results collector ─────────────────────────────────────────────
_RESULTS = []


# ─────────────────────────────────────────────────────────────────────────────
# Session-level fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def base_url():
    return config.BASE_URL


# ─────────────────────────────────────────────────────────────────────────────
# Function-level WebDriver fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def driver():
    """Fresh WebDriver per test function."""
    drv = create_driver()
    yield drv
    drv.quit()


@pytest.fixture(scope="function")
def driver_wide(driver):
    """Desktop-wide viewport."""
    driver.set_window_size(1920, 1080)
    yield driver


@pytest.fixture(scope="function")
def driver_mobile(driver):
    """Mobile viewport."""
    w, h = config.VIEWPORTS["mobile"]
    driver.set_window_size(w, h)
    yield driver


@pytest.fixture(scope="function")
def driver_tablet(driver):
    """Tablet viewport."""
    w, h = config.VIEWPORTS["tablet"]
    driver.set_window_size(w, h)
    yield driver


# ─────────────────────────────────────────────────────────────────────────────
# Page-level fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def login_page(driver):
    return LoginPage(driver)


@pytest.fixture(scope="function")
def dashboard_page(driver):
    return DashboardPage(driver)


@pytest.fixture(scope="function")
def farmers_page(driver):
    return FarmersPage(driver)


@pytest.fixture(scope="function")
def disease_alerts_page(driver):
    return DiseaseAlertsPage(driver)


@pytest.fixture(scope="function")
def analytics_page(driver):
    return AnalyticsPage(driver)


@pytest.fixture(scope="function")
def map_page(driver):
    return MapPage(driver)


@pytest.fixture(scope="function")
def unauthorized_page(driver):
    return UnauthorizedPage(driver)


# ─────────────────────────────────────────────────────────────────────────────
# Authenticated session fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def authenticated_officer(driver):
    """Opens login page and logs in as officer, yields driver."""
    page = LoginPage(driver)
    page.load()
    page.login_as_officer()
    page.wait_for_url_contains("dashboard")
    yield driver


@pytest.fixture(scope="function")
def authenticated_admin(driver):
    """Opens login page and logs in as admin, yields driver."""
    page = LoginPage(driver)
    page.load()
    page.login_as_admin()
    page.wait_for_url_contains("dashboard")
    yield driver


@pytest.fixture(scope="function")
def officer_dashboard(authenticated_officer):
    """Returns DashboardPage already authenticated as officer."""
    return DashboardPage(authenticated_officer)


@pytest.fixture(scope="function")
def officer_farmers(authenticated_officer):
    """Returns FarmersPage already authenticated as officer."""
    return FarmersPage(authenticated_officer)


@pytest.fixture(scope="function")
def officer_disease_alerts(authenticated_officer):
    """Returns DiseaseAlertsPage already authenticated as officer."""
    return DiseaseAlertsPage(authenticated_officer)


@pytest.fixture(scope="function")
def officer_analytics(authenticated_officer):
    """Returns AnalyticsPage already authenticated as officer."""
    return AnalyticsPage(authenticated_officer)


@pytest.fixture(scope="function")
def officer_map(authenticated_officer):
    """Returns MapPage already authenticated as officer."""
    return MapPage(authenticated_officer)


# ─────────────────────────────────────────────────────────────────────────────
# Auto-screenshot on failure
# ─────────────────────────────────────────────────────────────────────────────

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep     = outcome.get_result()

    if rep.when == "call" and rep.failed:
        drv = item.funcargs.get("driver") or \
              item.funcargs.get("authenticated_officer") or \
              item.funcargs.get("authenticated_admin")
        if drv:
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = item.nodeid.replace("::", "_").replace("/", "_").replace("\\", "_")
            path = os.path.join(config.SCREENSHOTS_DIR, f"FAIL_{name}_{ts}.png")
            try:
                drv.save_screenshot(path)
                logger.info("Failure screenshot: %s", path)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# JSON result collection
# ─────────────────────────────────────────────────────────────────────────────

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    start = time.time()
    outcome = yield
    duration = round(time.time() - start, 3)

    rep = getattr(item, "_report_sections", [])
    status = "SKIPPED"
    for phase in ("setup", "call", "teardown"):
        report = getattr(item, f"_report_{phase}", None)
        if report and report.passed:
            status = "PASSED"
        elif report and report.failed:
            status = "FAILED"
            break

    markers = [m.name for m in item.iter_markers()]
    _RESULTS.append({
        "id":       item.nodeid,
        "module":   item.module.__name__ if item.module else "",
        "markers":  markers,
        "status":   status,
        "duration": duration,
    })


def pytest_sessionfinish(session, exitstatus):
    """Write execution-results.json after entire session."""
    results = {
        "run_at":  datetime.now().isoformat(),
        "base_url": config.BASE_URL,
        "total":   len(_RESULTS),
        "passed":  sum(1 for r in _RESULTS if r["status"] == "PASSED"),
        "failed":  sum(1 for r in _RESULTS if r["status"] == "FAILED"),
        "skipped": sum(1 for r in _RESULTS if r["status"] == "SKIPPED"),
        "tests":   _RESULTS,
    }
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    with open(config.JSON_REPORT, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    logger.info("JSON results written to %s", config.JSON_REPORT)
