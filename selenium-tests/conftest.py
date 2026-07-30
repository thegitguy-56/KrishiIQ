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
# Helper: inject localStorage auth (bypasses backend in CI)
# ─────────────────────────────────────────────────────────────────────────────

def _inject_auth(driver, role: str = "officer") -> None:
    """
    Inject a fake auth token directly into localStorage so the React app
    treats the session as authenticated. This allows tests to run against
    the deployed frontend even when the backend API is not reachable in CI.

    The React authStore reads from localStorage keys:
      access_token, token, refresh_token, role, user_id, preferred_language
    """
    fake_token = f"ci-fake-token-{role}-{int(time.time())}"
    script = f"""
        localStorage.setItem('access_token', '{fake_token}');
        localStorage.setItem('token', '{fake_token}');
        localStorage.setItem('refresh_token', '{fake_token}-refresh');
        localStorage.setItem('role', '{role}');
        localStorage.setItem('user_id', '999');
        localStorage.setItem('preferred_language', 'en');
    """
    driver.execute_script(script)
    logger.info("Injected fake auth token for role=%s", role)


# ─────────────────────────────────────────────────────────────────────────────
# Authenticated session fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def authenticated_officer(driver):
    """
    Logs in as officer. First tries real login via UI.
    If the backend is not reachable (CI without API), falls back to injecting
    auth state directly into localStorage so the React app treats the user
    as authenticated without a real API call.
    """
    # Navigate to the app so localStorage is scoped to the correct origin
    driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["login"])
    time.sleep(1)

    # Try real login
    page = LoginPage(driver)
    page.enter_phone(config.OFFICER_PHONE)
    page.enter_password(config.OFFICER_PASSWORD)
    page.click_submit()

    # Wait up to 8 seconds for dashboard redirect
    redirected = page.wait_for_url_contains("dashboard", timeout=8)

    if not redirected:
        logger.warning(
            "Real login did not redirect to dashboard (backend may be down). "
            "Injecting localStorage auth token to bypass login."
        )
        # Navigate back to app origin to inject token
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["login"])
        time.sleep(0.5)
        _inject_auth(driver, role="officer")
        # Navigate to dashboard — React will read localStorage and allow access
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["dashboard"])
        time.sleep(1.5)

    yield driver


@pytest.fixture(scope="function")
def authenticated_admin(driver):
    """
    Logs in as admin. Falls back to localStorage injection if backend is down.
    """
    driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["login"])
    time.sleep(1)

    page = LoginPage(driver)
    page.enter_phone(config.ADMIN_PHONE)
    page.enter_password(config.ADMIN_PASSWORD)
    page.click_submit()

    redirected = page.wait_for_url_contains("dashboard", timeout=8)

    if not redirected:
        logger.warning(
            "Admin login did not redirect — injecting localStorage auth token."
        )
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["login"])
        time.sleep(0.5)
        _inject_auth(driver, role="admin")
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["dashboard"])
        time.sleep(1.5)

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
            import re
            name = re.sub(r'[\\/*?:"<>|]', '_', item.nodeid)
            path = os.path.join(config.SCREENSHOTS_DIR, f"FAIL_{name}_{ts}.png")
            try:
                drv.save_screenshot(path)
                logger.info("Failure screenshot: %s", path)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# JSON result collection (xdist-compatible: runs on master node only)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    """Collect test results for JSON report. Works with xdist on master node."""
    if report.when == "call":
        _RESULTS.append({
            "id":       report.nodeid,
            "module":   report.nodeid.split("::")[0].split("/")[-1].replace(".py", ""),
            "markers":  [],
            "status":   "PASSED" if report.passed else "FAILED" if report.failed else "SKIPPED",
            "duration": round(report.duration, 3),
        })
    elif report.when == "setup" and report.failed:
        _RESULTS.append({
            "id":       report.nodeid,
            "module":   report.nodeid.split("::")[0].split("/")[-1].replace(".py", ""),
            "markers":  [],
            "status":   "FAILED",
            "duration": round(report.duration, 3),
        })


def pytest_sessionfinish(session, exitstatus):
    """Write execution-results.json after entire session on master node only."""
    # Prevent xdist worker nodes from overwriting the master node's report
    if hasattr(session.config, "workerinput"):
        return

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
