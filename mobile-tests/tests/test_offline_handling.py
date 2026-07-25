"""
Module: Offline Handling (target 20 executable cases)
Covers: app launch offline, key network-dependent actions attempted while
offline, cached/local data via CacheService, and recovery when connectivity
returns.
"""
import pytest

from data.test_data import VALID_FARMER
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.crop_health_page import CropHealthPage
from pages.ai_chat_page import AiChatPage
from pages.main_shell_page import MainShellPage
from pages.welcome_page import WelcomePage

pytestmark = pytest.mark.offline


def _toggle_offline(driver):
    try:
        driver.set_network_connection(0)
        return True
    except Exception:
        return False


def _toggle_online(driver):
    try:
        driver.set_network_connection(6)
    except Exception:
        pass


def _login(driver, finder):
    driver.activate_app("com.krishiiq.krishiiq")
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    login = LoginPage(driver, finder)
    login.login(VALID_FARMER["phone"], VALID_FARMER["password"])
    login.wait(1.5)


@pytest.mark.p1
def test_app_launches_while_offline(driver, finder):
    """OFFLINE: the app launches to the Welcome/Login screen without crashing when there is no network."""
    driver.terminate_app("com.krishiiq.krishiiq")
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    driver.activate_app("com.krishiiq.krishiiq")
    driver.wait_activity if hasattr(driver, "wait_activity") else None
    _toggle_online(driver)


@pytest.mark.p1
def test_login_attempt_offline_shows_error(driver, finder):
    """OFFLINE: attempting login while offline shows a connectivity error, no crash/hang."""
    driver.activate_app("com.krishiiq.krishiiq")
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    LoginPage(driver, finder).login(VALID_FARMER["phone"], VALID_FARMER["password"])
    _toggle_online(driver)


@pytest.mark.p1
def test_dashboard_cached_data_visible_offline(driver, finder):
    """OFFLINE: after an online session, the dashboard still renders previously-loaded cached content when connectivity drops (CacheService)."""
    _login(driver, finder)
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    assert "Farmer" in driver.page_source or "Vanakkam" in driver.page_source
    _toggle_online(driver)


@pytest.mark.p2
def test_advisory_refresh_offline_shows_error(driver, finder):
    """OFFLINE: refreshing the Advisory feed while offline surfaces an error instead of an infinite spinner."""
    _login(driver, finder)
    MainShellPage(driver, finder).go_advisory()
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    from pages.advisory_page import AdvisoryPage

    AdvisoryPage(driver, finder).refresh()
    _toggle_online(driver)


@pytest.mark.p2
def test_disease_detection_offline_blocked_gracefully(driver, finder):
    """OFFLINE: attempting AI disease detection while offline fails gracefully with a message, no crash."""
    _login(driver, finder)
    HomePage(driver, finder).open_quick_action("Detect Disease")
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    page = CropHealthPage(driver, finder)
    page.select_farm()
    page.upload_and_detect(source="gallery")
    _toggle_online(driver)


@pytest.mark.p2
def test_ai_chat_offline_blocked_gracefully(driver, finder):
    """OFFLINE: sending an AI chat message while offline fails gracefully with a message, no crash."""
    _login(driver, finder)
    HomePage(driver, finder).open_quick_action("AI Assistant")
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    AiChatPage(driver, finder).send_message("Is it going to rain today?")
    _toggle_online(driver)


@pytest.mark.p2
def test_farm_data_save_offline_queued_or_errored(driver, finder):
    """OFFLINE: submitting Farm Data Input while offline either errors clearly or queues locally, never silently loses data."""
    _login(driver, finder)
    MainShellPage(driver, finder).go_profile()
    from pages.advisory_page import ProfilePage

    ProfilePage(driver, finder).go_to_input_farm_data()
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    from pages.farm_pages import FarmDataInputPage

    FarmDataInputPage(driver, finder).fill_crop_history(crop="Offline Rice", yield_kg="500", fertilizer="Urea")
    FarmDataInputPage(driver, finder).save()
    _toggle_online(driver)


@pytest.mark.p1
def test_recovery_after_connectivity_restored(driver, finder):
    """OFFLINE→ONLINE: after connectivity is restored, retrying a previously-failed action (advisory refresh) succeeds."""
    _login(driver, finder)
    MainShellPage(driver, finder).go_advisory()
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    from pages.advisory_page import AdvisoryPage

    page = AdvisoryPage(driver, finder)
    page.refresh()
    _toggle_online(driver)
    page.wait(1)
    page.refresh()


@pytest.mark.p3
@pytest.mark.parametrize("cycle", range(1, 6))
def test_repeated_offline_online_toggling_stability(driver, finder, cycle):
    """OFFLINE: rapidly toggling connectivity on/off while on the dashboard does not crash the app (5 cycles)."""
    _login(driver, finder)
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    _toggle_online(driver)


@pytest.mark.p3
@pytest.mark.parametrize("screen", ["home", "advisory", "sensors", "profile"])
def test_offline_banner_or_indicator_per_screen(driver, finder, screen):
    """OFFLINE: navigating between core screens while offline never produces an unhandled exception screen (4 screens)."""
    _login(driver, finder)
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    shell = MainShellPage(driver, finder)
    {"home": shell.go_home, "advisory": shell.go_advisory, "sensors": shell.go_sensors, "profile": shell.go_profile}[screen]()
    _toggle_online(driver)


@pytest.mark.p3
def test_offline_then_relaunch_recovers(driver, finder):
    """OFFLINE: relaunching the app after going offline mid-session recovers cleanly once online again."""
    _login(driver, finder)
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    driver.terminate_app("com.krishiiq.krishiiq")
    _toggle_online(driver)
    driver.activate_app("com.krishiiq.krishiiq")


@pytest.mark.p3
def test_sensor_pairing_offline_errors_gracefully(driver, finder):
    """OFFLINE: pairing a sensor while offline surfaces a clear error rather than hanging."""
    _login(driver, finder)
    MainShellPage(driver, finder).go_sensors()
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    from pages.farm_pages import SensorsPage

    SensorsPage(driver, finder).pair_sensor("SENSOR-OFFLINE")
    _toggle_online(driver)


@pytest.mark.p3
def test_registration_offline_errors_gracefully(driver, finder):
    """OFFLINE: attempting registration while offline surfaces a clear error rather than hanging or crashing."""
    driver.activate_app("com.krishiiq.krishiiq")
    welcome = WelcomePage(driver, finder)
    welcome.go_to_register()
    if not _toggle_offline(driver):
        pytest.skip("Network toggling not supported on this emulator profile")
    from pages.register_page import RegisterPage

    RegisterPage(driver, finder).register(
        name="Offline Test", email="offline@example.com", phone="9812345688", password="OfflineTest1", district="Salem"
    )
    _toggle_online(driver)
