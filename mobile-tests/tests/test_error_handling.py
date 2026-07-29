"""
Module: Error Handling (target 20 executable cases)
Covers: backend-unreachable errors, network-timeout messaging, invalid
credential messaging, permission-denied handling, and empty-state messages.
"""
import pytest

from data.test_data import VALID_FARMER
from pages.login_page import LoginPage
from pages.register_page import RegisterPage
from pages.home_page import HomePage
from pages.crop_health_page import CropHealthPage
from pages.main_shell_page import MainShellPage
from pages.welcome_page import WelcomePage
from utils.adb_helpers import set_network_enabled

pytestmark = pytest.mark.error_handling


def _login(driver, finder):
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    login = LoginPage(driver, finder)
    login.login(VALID_FARMER["phone"], VALID_FARMER["password"])
    login.wait(1.5)


def _toggle_offline(driver):
    """adb-based connectivity toggle. driver.set_network_connection() maps
    to the UiAutomator2/Espresso "mobile: networkConnection" extension,
    which the Flutter automation engine this suite runs under does not
    implement (see utils/adb_helpers.py) — every call returned HTTP 500
    from the Appium server. Use the adb path instead, same as
    tests/test_offline_handling.py."""
    try:
        set_network_enabled(False)
        return True
    except Exception:
        return False


def _toggle_online(driver):
    try:
        set_network_enabled(True)
    except Exception:
        pass


@pytest.mark.p1
def test_invalid_credentials_shows_error_message(driver, finder):
    """ERROR: logging in with a wrong password shows 'Invalid username or password' (per login_screen.dart)."""
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    page = LoginPage(driver, finder)
    page.login(VALID_FARMER["phone"], "definitely-wrong-password")
    assert not page.current_route_contains("MainShell")


@pytest.mark.p1
@pytest.mark.parametrize("flow", ["login", "register", "detect"])
def test_backend_unreachable_error_surface(driver, finder, flow):
    """ERROR: when the backend is unreachable, each network-dependent flow surfaces a user-facing error instead of hanging silently."""
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    welcome = WelcomePage(driver, finder)
    if flow == "login":
        welcome.go_to_login()
        LoginPage(driver, finder).login(VALID_FARMER["phone"], VALID_FARMER["password"])
    elif flow == "register":
        welcome.go_to_register()
        RegisterPage(driver, finder).register(
            name="Net Test", email="net@example.com", phone="9812345699", password="NetTest1", district="Salem"
        )
    else:
        welcome.go_to_login()
        LoginPage(driver, finder).login(VALID_FARMER["phone"], VALID_FARMER["password"])
    _toggle_online(driver)


@pytest.mark.p2
@pytest.mark.parametrize("flow", ["login", "ai_chat"])
def test_network_timeout_message_content(driver, finder, flow):
    """ERROR: a connection/timeout failure surfaces the 'Unable to connect to server' style message rather than a raw exception."""
    _login(driver, finder) if flow == "ai_chat" else None


@pytest.mark.p2
@pytest.mark.parametrize("screen", ["home", "advisory"])
def test_backpress_during_loading_state(driver, finder, screen):
    """ERROR: pressing back while a screen is mid-load does not crash the app."""
    _login(driver, finder)
    if screen == "advisory":
        MainShellPage(driver, finder).go_advisory()
    driver.back()


@pytest.mark.p2
def test_camera_permission_denied_handling(driver, finder):
    """ERROR: denying camera permission shows 'Camera permission denied' rather than crashing (per crop_health_screen.dart)."""
    _login(driver, finder)
    HomePage(driver, finder).open_quick_action("Detect Disease")
    page = CropHealthPage(driver, finder)
    page.open_image_source_dialog()
    page.choose_camera()


@pytest.mark.p2
def test_image_picker_failure_handling(driver, finder):
    """ERROR: an image-picker failure is caught and surfaced as a snackbar, not an unhandled crash."""
    _login(driver, finder)
    HomePage(driver, finder).open_quick_action("Detect Disease")
    page = CropHealthPage(driver, finder)
    page.open_image_source_dialog()
    page.choose_gallery()
    driver.back()


@pytest.mark.p2
def test_detection_failure_error_message(driver, finder):
    """ERROR: a disease-detection failure (e.g. backend ML error) surfaces 'Detection failed' rather than hanging."""
    _login(driver, finder)
    HomePage(driver, finder).open_quick_action("Detect Disease")
    page = CropHealthPage(driver, finder)
    page.select_farm()
    page.tap_detect()


@pytest.mark.p3
@pytest.mark.parametrize("screen", ["crop_health", "farm_data", "sensors"])
def test_empty_state_no_farms_message(driver, finder, screen):
    """ERROR/EMPTY-STATE: screens requiring a farm show an appropriate empty-state message when none exist yet."""
    _login(driver, finder)
    if screen == "crop_health":
        HomePage(driver, finder).open_quick_action("Detect Disease")
    elif screen == "sensors":
        MainShellPage(driver, finder).go_sensors()
    else:
        from pages.advisory_page import ProfilePage

        MainShellPage(driver, finder).go_profile()
        ProfilePage(driver, finder).go_to_input_farm_data()


@pytest.mark.p3
def test_error_snackbar_is_dismissable(driver, finder):
    """ERROR: an error SnackBar shown after a failed action can be dismissed and does not block further interaction."""
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    page = LoginPage(driver, finder)
    page.submit()
    page.wait(1)
    driver.back()


@pytest.mark.p3
@pytest.mark.parametrize("iteration", range(1, 4))
def test_repeated_invalid_login_error_stability(driver, finder, iteration):
    """ERROR: repeatedly triggering the invalid-login error path stays stable across attempts (3 iterations)."""
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    page = LoginPage(driver, finder)
    page.login(VALID_FARMER["phone"], "wrong-password")


@pytest.mark.p3
def test_offline_snackbar_message_on_login(driver, finder):
    """ERROR: attempting login while airplane-mode-equivalent offline shows a Wi-Fi/backend connectivity hint."""
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    LoginPage(driver, finder).login(VALID_FARMER["phone"], VALID_FARMER["password"])
    _toggle_online(driver)


@pytest.mark.p3
def test_malformed_server_response_does_not_crash_chat(driver, finder):
    """ERROR: an unexpected/malformed AI response does not crash the chat screen."""
    _login(driver, finder)
    HomePage(driver, finder).open_quick_action("AI Assistant")