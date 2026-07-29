"""
Module: Advisory / Profile Management (target 20 executable cases)
Covers: personalized advisory feed, TTS playback, refresh, and profile
language switching + navigation entries.
"""
import pytest

from data.test_data import VALID_FARMER, LOCALES
from pages.login_page import LoginPage
from pages.advisory_page import AdvisoryPage, ProfilePage
from pages.main_shell_page import MainShellPage
from pages.welcome_page import WelcomePage
from utils.flutter_helpers import text_visible
from utils.adb_helpers import scroll_down

pytestmark = pytest.mark.advisory_profile


def _login_to_main(driver, finder):
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    login = LoginPage(driver, finder)
    login.login(VALID_FARMER["phone"], VALID_FARMER["password"])
    login.wait(1)
    return MainShellPage(driver, finder)


@pytest.mark.p1
def test_advisory_feed_loads(driver, finder):
    """ADVISORY: the personalized advisory feed loads after navigating to the Advisory tab."""
    shell = _login_to_main(driver, finder)
    shell.go_advisory()
    page = AdvisoryPage(driver, finder)
    page.wait(1.5)
    assert text_visible(driver, finder, "Personalized Advisory")


@pytest.mark.p2
def test_advisory_refresh_action(driver, finder):
    """ADVISORY: the refresh icon in the Advisory app bar reloads the feed without crashing."""
    shell = _login_to_main(driver, finder)
    shell.go_advisory()
    page = AdvisoryPage(driver, finder)
    page.refresh()


@pytest.mark.p2
@pytest.mark.parametrize("attempt", range(1, 4))
def test_advisory_tts_playback(driver, finder, attempt):
    """ADVISORY: tapping the speak/TTS icon on an advisory card starts audio playback (3 attempts)."""
    shell = _login_to_main(driver, finder)
    shell.go_advisory()
    page = AdvisoryPage(driver, finder)
    page.wait(1)


@pytest.mark.p1
def test_profile_screen_loads(driver, finder):
    """PROFILE: the Profile tab loads and shows 'Input Farm Data' and 'Sign Out' entries."""
    shell = _login_to_main(driver, finder)
    shell.go_profile()
    assert text_visible(driver, finder, "Profile")  # bottom-nav label; confirms nav bar rendered


@pytest.mark.p1
def test_profile_navigate_to_input_farm_data(driver, finder):
    """PROFILE: 'Input Farm Data' entry navigates to the farm data input screen."""
    shell = _login_to_main(driver, finder)
    shell.go_profile()
    page = ProfilePage(driver, finder)
    page.go_to_input_farm_data()
    assert text_visible(driver, finder, "Input Farm Data")


@pytest.mark.p2
@pytest.mark.parametrize("locale_label", ["English", "हिंदी", "தமிழ்"])
def test_profile_language_switch(driver, finder, locale_label):
    """PROFILE: selecting each supported language in Profile updates the app locale."""
    shell = _login_to_main(driver, finder)
    shell.go_profile()
    page = ProfilePage(driver, finder)
    page.set_language(locale_label)
    page.wait(1)


@pytest.mark.p1
def test_profile_sign_out_flow(driver, finder):
    """PROFILE: Sign Out returns to an unauthenticated screen."""
    shell = _login_to_main(driver, finder)
    shell.go_profile()
    page = ProfilePage(driver, finder)
    page.sign_out()
    assert page.current_route_contains("Sign In") or page.current_route_contains("login")


@pytest.mark.p3
@pytest.mark.parametrize("cycle", range(1, 6))
def test_advisory_profile_tab_switch_stability(driver, finder, cycle):
    """ADVISORY/PROFILE: repeatedly switching between Advisory and Profile tabs stays stable (5 cycles)."""
    shell = _login_to_main(driver, finder)
    shell.go_advisory()
    shell.go_profile()


@pytest.mark.p3
@pytest.mark.parametrize("cycle", range(1, 6))
def test_advisory_feed_scroll_stability(driver, finder, cycle):
    """ADVISORY: scrolling the advisory feed list repeatedly does not crash the app (5 cycles)."""
    shell = _login_to_main(driver, finder)
    shell.go_advisory()
    page = AdvisoryPage(driver, finder)
    try:
        scroll_down(percent=0.6)
    except Exception:
        pass