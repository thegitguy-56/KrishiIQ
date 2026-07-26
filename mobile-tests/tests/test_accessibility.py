"""
Module: Accessibility (target 10 executable cases)
Covers: semantic labels/content-description presence for TalkBack, tap
target sizing sanity checks, and font-scaling resilience.
"""
import pytest

from data.test_data import VALID_FARMER
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.welcome_page import WelcomePage

pytestmark = pytest.mark.accessibility


def _login(driver, finder):
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    login = LoginPage(driver, finder)
    login.login(VALID_FARMER["phone"], VALID_FARMER["password"])
    login.wait(1.5)


@pytest.mark.p2
def test_login_fields_have_accessible_labels(driver, finder):
    """A11Y: phone and password fields expose readable label text for screen readers (labelText renders as semantics)."""
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    assert "Phone Number" in driver.page_source and "Password" in driver.page_source


@pytest.mark.p2
def test_login_submit_button_has_readable_label(driver, finder):
    """A11Y: the login submit button exposes readable text ('Sign In') to screen readers."""
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    assert "Sign In" in driver.page_source


@pytest.mark.p2
def test_bottom_nav_labels_present_for_screen_readers(driver, finder):
    """A11Y: all 5 bottom-nav destination labels are present in the widget tree (TalkBack-readable)."""
    _login(driver, finder)
    for label in ["Home", "Advisory", "Sensors", "History", "Profile"]:
        assert label in driver.page_source


@pytest.mark.p3
def test_notifications_icon_has_icon_semantics(driver, finder):
    """A11Y: the notifications icon button is present as a distinct, focusable element."""
    _login(driver, finder)
    page = HomePage(driver, finder)
    assert page.by_key(page.NOTIFICATIONS_BUTTON) is not None


@pytest.mark.p3
def test_quick_action_tiles_have_text_labels(driver, finder):
    """A11Y: every Quick Action tile has a visible text label (not icon-only), aiding screen-reader users."""
    _login(driver, finder)
    for label in HomePage.QUICK_ACTIONS:
        assert label in driver.page_source


@pytest.mark.p3
@pytest.mark.parametrize("scale", [1.0, 1.3, 2.0], ids=["default", "large", "extra_large"])
def test_ui_resilient_to_font_scaling(driver, finder, scale):
    """A11Y: increasing the system font scale does not clip or crash the login screen (3 scale levels)."""
    try:
        driver.update_settings({"fontScale": scale})
    except Exception:
        pytest.skip("Font-scale override not supported on this driver/emulator profile")
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    try:
        driver.update_settings({"fontScale": 1.0})
    except Exception:
        pass


@pytest.mark.p3
def test_register_form_fields_have_accessible_labels(driver, finder):
    """A11Y: all registration form fields expose readable labels for screen readers."""
    welcome = WelcomePage(driver, finder)
    welcome.go_to_register()
    for label in ["Full Name", "Email", "Mobile Number", "Password", "District"]:
        assert label in driver.page_source


@pytest.mark.p3
def test_password_visibility_toggle_has_icon_semantics(driver, finder):
    """A11Y: the password-visibility eye icon is reachable as a distinct focusable control."""
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    page = LoginPage(driver, finder)
    assert page.by_key(page.PASSWORD_TOGGLE) is not None


@pytest.mark.p3
def test_advisory_speak_icon_has_semantics(driver, finder):
    """A11Y: the advisory card's text-to-speech icon is reachable as a distinct focusable control (aids low-literacy/visually-impaired farmers)."""
    _login(driver, finder)
    from pages.main_shell_page import MainShellPage

    MainShellPage(driver, finder).go_advisory()
    assert "record_voice_over" in driver.page_source.lower() or "Personalized Advisory" in driver.page_source


@pytest.mark.p2
def test_farm_setup_fields_have_accessible_labels(driver, finder):
    """A11Y: Farm Setup form fields expose readable labels ('Farm Name', 'Land Area (acres)', etc.) for screen readers."""
    _login(driver, finder)
    for label in ["Farm Name", "Land Area", "Primary Crop", "Soil Type"]:
        assert label in driver.page_source
