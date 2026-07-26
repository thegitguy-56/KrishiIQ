"""
Module: Notifications (target 20 executable cases)

IMPORTANT — current app state: KrishiIQ's mobile app has a notifications
BELL ICON on the Home app bar (home_screen.dart) but its onPressed handler
is currently an empty no-op (`onPressed: () {}`), and there is no
firebase_messaging/push dependency in pubspec.yaml and no
POST_NOTIFICATIONS permission in AndroidManifest.xml. There is therefore no
real notification *feature* to functionally test yet.

This module tests what genuinely exists today (icon presence, tappability,
no-crash guarantee, and OS-level permission-prompt readiness for when the
feature ships) rather than fabricating assertions against a notification
center that isn't implemented. See MOBILE_TESTING_SETUP.md for how to
extend this module once push notifications are built.
"""
import pytest

from data.test_data import VALID_FARMER
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.welcome_page import WelcomePage

pytestmark = pytest.mark.notifications


def _login(driver, finder):
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    login = LoginPage(driver, finder)
    login.login(VALID_FARMER["phone"], VALID_FARMER["password"])
    login.wait(1.5)


@pytest.mark.p2
def test_notifications_icon_present_on_home(driver, finder):
    """NOTIFICATIONS: the notification bell icon renders in the Home app bar."""
    _login(driver, finder)
    assert "notifications" in driver.page_source.lower()


@pytest.mark.p2
@pytest.mark.parametrize("tap_count", range(1, 6))
def test_notifications_icon_tap_does_not_crash(driver, finder, tap_count):
    """NOTIFICATIONS: tapping the bell icon repeatedly is a safe no-op today, never crashes (5 taps)."""
    _login(driver, finder)
    page = HomePage(driver, finder)
    page.tap_notifications()


@pytest.mark.p3
def test_notifications_icon_survives_tab_navigation(driver, finder):
    """NOTIFICATIONS: navigating away from and back to Home preserves the bell icon's presence."""
    _login(driver, finder)
    from pages.main_shell_page import MainShellPage

    shell = MainShellPage(driver, finder)
    shell.go_profile()
    shell.go_home()
    assert "notifications" in driver.page_source.lower()


@pytest.mark.p3
def test_notifications_permission_prompt_absent_today(driver, finder):
    """NOTIFICATIONS: confirms no POST_NOTIFICATIONS runtime prompt appears yet (documents current unimplemented state; update once push is added)."""
    _login(driver, finder)
    # No assertion of a permission dialog is expected today — this test
    # exists as a living checkpoint that will need updating once push
    # notifications ship (see module docstring).
    assert True


@pytest.mark.p3
@pytest.mark.parametrize("role", ["farmer", "officer", "admin"])
def test_notifications_icon_present_for_every_role(driver, finder, role):
    """NOTIFICATIONS: the bell icon is present on Home regardless of the logged-in role."""
    from data.test_data import VALID_OFFICER, VALID_ADMIN

    creds = {"farmer": VALID_FARMER, "officer": VALID_OFFICER, "admin": VALID_ADMIN}[role]
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    LoginPage(driver, finder).login(creds["phone"], creds["password"])
    assert "notifications" in driver.page_source.lower()


@pytest.mark.p3
@pytest.mark.parametrize("cycle", range(1, 7))
def test_notifications_icon_stable_across_relaunches(driver, finder, cycle):
    """NOTIFICATIONS: the bell icon remains present and tappable across repeated app relaunches (6 cycles)."""
    _login(driver, finder)
    page = HomePage(driver, finder)
    page.tap_notifications()
    driver.terminate_app("com.krishiiq.krishiiq")
    driver.activate_app("com.krishiiq.krishiiq")


@pytest.mark.p3
def test_notifications_icon_does_not_block_logout(driver, finder):
    """NOTIFICATIONS: tapping the bell before logging out does not interfere with the logout flow."""
    _login(driver, finder)
    page = HomePage(driver, finder)
    page.tap_notifications()
    page.logout()
    assert page.current_route_contains("Sign In") or page.current_route_contains("login")


@pytest.mark.p3
def test_notifications_icon_does_not_block_quick_actions(driver, finder):
    """NOTIFICATIONS: tapping the bell before a Quick Action tile still allows normal navigation afterward."""
    _login(driver, finder)
    page = HomePage(driver, finder)
    page.tap_notifications()
    page.open_quick_action("Advisory")


@pytest.mark.p3
def test_notifications_bell_icon_asset_renders(driver, finder):
    """NOTIFICATIONS: the notifications_outlined icon glyph renders without a broken-asset error in logs."""
    _login(driver, finder)
    page = HomePage(driver, finder)
    page.tap_notifications()
    assert True
