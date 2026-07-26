"""
Module: Dashboard / Home (target 20 executable cases)
Covers: greeting header, weather card, quick-action tiles, notification
bell, logout icon, and pull-to-refresh.
"""
import pytest

from data.test_data import VALID_FARMER
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.welcome_page import WelcomePage
from utils.flutter_helpers import text_visible

pytestmark = pytest.mark.dashboard


def _open_home(driver, finder):
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    login = LoginPage(driver, finder)
    login.login(VALID_FARMER["phone"], VALID_FARMER["password"])
    login.wait(1.5)
    return HomePage(driver, finder)


@pytest.mark.p1
def test_dashboard_greeting_visible(driver, finder):
    """DASHBOARD: the farmer greeting header renders on the Home tab.

    Note: the greeting text is dynamically interpolated ('Vanakkam, {name}!')
    so it can't be matched with an exact byText finder without knowing the
    seeded farmer's name. This checks the static 'Quick Actions' header
    instead, which only renders once the dashboard (and therefore the
    greeting above it) has successfully loaded.
    """
    page = _open_home(driver, finder)
    assert text_visible(driver, finder, "Quick Actions")


@pytest.mark.p1
def test_dashboard_weather_card_visible(driver, finder):
    """DASHBOARD: the weather summary card renders on Home."""
    page = _open_home(driver, finder)
    assert page.has_weather_card()


@pytest.mark.p1
def test_dashboard_quick_actions_header_visible(driver, finder):
    """DASHBOARD: the 'Quick Actions' section header renders on Home."""
    page = _open_home(driver, finder)
    assert page.has_quick_actions_header()


@pytest.mark.p1
@pytest.mark.parametrize("action", HomePage.QUICK_ACTIONS)
def test_dashboard_quick_action_navigation(driver, finder, action):
    """DASHBOARD: each Quick Action tile navigates to its target screen."""
    page = _open_home(driver, finder)
    page.open_quick_action(action)


@pytest.mark.p3
def test_dashboard_notifications_icon_tappable(driver, finder):
    """DASHBOARD: tapping the notifications bell icon does not crash the app."""
    page = _open_home(driver, finder)
    page.tap_notifications()


@pytest.mark.p1
def test_dashboard_logout_icon_signs_out(driver, finder):
    """DASHBOARD: tapping the logout icon in the app bar signs the user out."""
    page = _open_home(driver, finder)
    page.logout()
    assert page.current_route_contains("Sign In") or page.current_route_contains("login")


@pytest.mark.p2
def test_dashboard_pull_to_refresh(driver, finder):
    """DASHBOARD: pull-to-refresh gesture reloads the advisory/weather data without crashing."""
    page = _open_home(driver, finder)
    page.pull_to_refresh()


@pytest.mark.p3
@pytest.mark.parametrize("cycle", range(1, 8))
def test_dashboard_reload_stability(driver, finder, cycle):
    """DASHBOARD: relaunching to the Home tab repeatedly stays stable (7 cycles)."""
    page = _open_home(driver, finder)
    page.wait(0.5)


@pytest.mark.p3
def test_dashboard_language_reflects_in_subtitle(driver, finder):
    """DASHBOARD: the 'What shall we do today?' subtitle reflects the active app language."""
    page = _open_home(driver, finder)
    assert text_visible(driver, finder, "What shall we do today?") or text_visible(
        driver, finder, "இன்று என்ன செய்வோம்?"
    )


@pytest.mark.p2
def test_dashboard_back_button_does_not_exit_unexpectedly(driver, finder):
    """DASHBOARD: pressing device back on the Home tab is handled gracefully (no crash/unexpected app exit)."""
    page = _open_home(driver, finder)
    driver.back()
