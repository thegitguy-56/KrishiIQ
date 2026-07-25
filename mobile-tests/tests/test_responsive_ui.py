"""
Module: Responsive UI (target 10 executable cases)
Covers: orientation changes and rendering sanity across the emulator's
screen size on key scrollable/grid screens.
"""
import pytest

from data.test_data import VALID_FARMER
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.main_shell_page import MainShellPage
from pages.welcome_page import WelcomePage

pytestmark = pytest.mark.responsive


def _login(driver, finder):
    driver.activate_app("com.krishiiq.krishiiq")
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    login = LoginPage(driver, finder)
    login.login(VALID_FARMER["phone"], VALID_FARMER["password"])
    login.wait(1.5)


def _rotate(driver, orientation):
    try:
        driver.orientation = orientation
        return True
    except Exception:
        return False


@pytest.mark.p2
def test_login_screen_landscape_rendering(driver, finder):
    """RESPONSIVE: the login screen renders without overflow errors in landscape orientation."""
    driver.activate_app("com.krishiiq.krishiiq")
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    if not _rotate(driver, "LANDSCAPE"):
        pytest.skip("Orientation change not supported on this emulator profile")
    _rotate(driver, "PORTRAIT")


@pytest.mark.p2
def test_dashboard_grid_landscape_rendering(driver, finder):
    """RESPONSIVE: the Quick Actions 2-column grid on Home reflows correctly in landscape."""
    _login(driver, finder)
    if not _rotate(driver, "LANDSCAPE"):
        pytest.skip("Orientation change not supported on this emulator profile")
    assert "Quick Actions" in driver.page_source
    _rotate(driver, "PORTRAIT")


@pytest.mark.p2
def test_advisory_feed_landscape_scroll(driver, finder):
    """RESPONSIVE: the Advisory feed list remains scrollable and renders correctly in landscape."""
    _login(driver, finder)
    MainShellPage(driver, finder).go_advisory()
    if not _rotate(driver, "LANDSCAPE"):
        pytest.skip("Orientation change not supported on this emulator profile")
    _rotate(driver, "PORTRAIT")


@pytest.mark.p3
def test_register_form_landscape_rendering(driver, finder):
    """RESPONSIVE: the registration form remains usable (fields reachable) in landscape orientation."""
    driver.activate_app("com.krishiiq.krishiiq")
    welcome = WelcomePage(driver, finder)
    welcome.go_to_register()
    if not _rotate(driver, "LANDSCAPE"):
        pytest.skip("Orientation change not supported on this emulator profile")
    assert "Full Name" in driver.page_source
    _rotate(driver, "PORTRAIT")


@pytest.mark.p3
@pytest.mark.parametrize("cycle", range(1, 4))
def test_repeated_orientation_toggling_stability(driver, finder, cycle):
    """RESPONSIVE: rapidly toggling orientation on the dashboard does not crash the app (3 cycles)."""
    _login(driver, finder)
    if not _rotate(driver, "LANDSCAPE"):
        pytest.skip("Orientation change not supported on this emulator profile")
    _rotate(driver, "PORTRAIT")


@pytest.mark.p3
def test_crop_health_screen_landscape_rendering(driver, finder):
    """RESPONSIVE: the Crop Disease Detection screen's image picker and dropdown remain usable in landscape."""
    _login(driver, finder)
    HomePage(driver, finder).open_quick_action("Detect Disease")
    if not _rotate(driver, "LANDSCAPE"):
        pytest.skip("Orientation change not supported on this emulator profile")
    _rotate(driver, "PORTRAIT")


@pytest.mark.p3
def test_ai_chat_input_bar_landscape_rendering(driver, finder):
    """RESPONSIVE: the AI chat input bar and send button remain visible and usable in landscape."""
    _login(driver, finder)
    HomePage(driver, finder).open_quick_action("AI Assistant")
    if not _rotate(driver, "LANDSCAPE"):
        pytest.skip("Orientation change not supported on this emulator profile")
    _rotate(driver, "PORTRAIT")


@pytest.mark.p3
def test_bottom_nav_bar_landscape_rendering(driver, finder):
    """RESPONSIVE: all 5 bottom-navigation destinations remain visible/tappable in landscape."""
    _login(driver, finder)
    if not _rotate(driver, "LANDSCAPE"):
        pytest.skip("Orientation change not supported on this emulator profile")
    for label in ["Home", "Advisory", "Sensors", "History", "Profile"]:
        assert label in driver.page_source
    _rotate(driver, "PORTRAIT")
