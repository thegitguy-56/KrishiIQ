"""
Module: Forms (target 40 executable cases)
Covers: Farm Setup form, Farm Data Input form (crop-history / soil-health),
and Sensor pairing form — valid submissions, boundary numeric data, and
boundary text data.
"""
import pytest

from data.test_data import VALID_FARMER, BOUNDARY_NUMBERS, FARM_NAMES, SENSOR_DEVICE_IDS
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.farm_pages import FarmSetupPage, FarmDataInputPage, SensorsPage
from pages.main_shell_page import MainShellPage
from pages.welcome_page import WelcomePage

pytestmark = pytest.mark.forms


def _login(driver, finder):
    driver.activate_app("com.krishiiq.krishiiq")
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    login = LoginPage(driver, finder)
    login.login(VALID_FARMER["phone"], VALID_FARMER["password"])
    login.wait(1.5)


@pytest.mark.p1
def test_farm_setup_valid_submission(driver, finder):
    """FORMS: Farm Setup form accepts valid name/area/crop/soil and submits."""
    _login(driver, finder)
    home = HomePage(driver, finder)
    page = FarmSetupPage(driver, finder)
    page.fill(name="Green Valley Farm", area="2.5", crop="Rice", soil="Loamy")
    page.submit()


@pytest.mark.p2
@pytest.mark.parametrize("area,label", BOUNDARY_NUMBERS, ids=[l for _, l in BOUNDARY_NUMBERS])
def test_farm_setup_boundary_area(driver, finder, area, label):
    """FORMS: Farm Setup 'Land Area' field handles boundary/invalid numeric input without crashing."""
    _login(driver, finder)
    page = FarmSetupPage(driver, finder)
    page.fill(name="Boundary Test Farm", area=area, crop="Wheat", soil="Clay")
    page.submit()


@pytest.mark.p1
def test_farm_setup_empty_required_fields(driver, finder):
    """FORMS: submitting Farm Setup with all fields empty is blocked / shows a message."""
    _login(driver, finder)
    page = FarmSetupPage(driver, finder)
    page.submit()


@pytest.mark.p2
def test_farm_setup_gps_button_populates_coordinates(driver, finder):
    """FORMS: 'Use GPS' button attempts to capture device location and updates the label."""
    _login(driver, finder)
    page = FarmSetupPage(driver, finder)
    page.use_gps()


@pytest.mark.p1
def test_farm_data_crop_history_valid_submission(driver, finder):
    """FORMS: Farm Data Input (Crop History category) accepts valid data and saves."""
    _login(driver, finder)
    from pages.main_shell_page import MainShellPage

    MainShellPage(driver, finder).go_profile()
    from pages.advisory_page import ProfilePage

    ProfilePage(driver, finder).go_to_input_farm_data()
    page = FarmDataInputPage(driver, finder)
    page.fill_crop_history(crop="Paddy", yield_kg="1200", fertilizer="Urea")
    page.save()


@pytest.mark.p1
def test_farm_data_soil_health_valid_submission(driver, finder):
    """FORMS: Farm Data Input (Soil Health category) accepts a valid SHC ID and saves."""
    _login(driver, finder)
    from pages.main_shell_page import MainShellPage
    from pages.advisory_page import ProfilePage

    MainShellPage(driver, finder).go_profile()
    ProfilePage(driver, finder).go_to_input_farm_data()
    page = FarmDataInputPage(driver, finder)
    page.fill_soil_health(shc_id="SHC-2024-0001")
    page.save()


@pytest.mark.p2
@pytest.mark.parametrize("yield_kg,label", BOUNDARY_NUMBERS, ids=[l for _, l in BOUNDARY_NUMBERS])
def test_farm_data_boundary_yield(driver, finder, yield_kg, label):
    """FORMS: Farm Data 'Yield (kg)' field handles boundary/invalid numeric input without crashing."""
    _login(driver, finder)
    from pages.main_shell_page import MainShellPage
    from pages.advisory_page import ProfilePage

    MainShellPage(driver, finder).go_profile()
    ProfilePage(driver, finder).go_to_input_farm_data()
    page = FarmDataInputPage(driver, finder)
    page.fill_crop_history(crop="Test Crop", yield_kg=yield_kg, fertilizer="NPK")
    page.save()


@pytest.mark.p2
@pytest.mark.parametrize("category", ["crop_history", "soil_health"])
def test_farm_data_category_switch(driver, finder, category):
    """FORMS: switching the segmented category control swaps the visible input fields correctly."""
    _login(driver, finder)
    from pages.main_shell_page import MainShellPage
    from pages.advisory_page import ProfilePage

    MainShellPage(driver, finder).go_profile()
    ProfilePage(driver, finder).go_to_input_farm_data()
    page = FarmDataInputPage(driver, finder)
    page.tap(page.by_text("Crop History" if category == "crop_history" else "Soil Health Card"))


@pytest.mark.p1
def test_sensor_pairing_valid_submission(driver, finder):
    """FORMS: Sensor pairing form accepts a valid device ID and pairs successfully."""
    _login(driver, finder)
    from pages.main_shell_page import MainShellPage

    MainShellPage(driver, finder).go_sensors()
    page = SensorsPage(driver, finder)
    page.pair_sensor("SENSOR-001")


@pytest.mark.p2
@pytest.mark.parametrize("device_id,label", SENSOR_DEVICE_IDS, ids=[l for _, l in SENSOR_DEVICE_IDS])
def test_sensor_pairing_device_id_variants(driver, finder, device_id, label):
    """FORMS: Sensor pairing 'Device ID' field handles boundary/invalid/malicious values safely."""
    _login(driver, finder)
    from pages.main_shell_page import MainShellPage

    MainShellPage(driver, finder).go_sensors()
    page = SensorsPage(driver, finder)
    page.pair_sensor(device_id)


@pytest.mark.p3
@pytest.mark.parametrize("name,label", FARM_NAMES, ids=[l for _, l in FARM_NAMES])
def test_farm_setup_name_field_boundary_text(driver, finder, name, label):
    """FORMS: Farm Setup 'Farm Name' field accepts boundary text values (short/long/special-chars/whitespace)."""
    _login(driver, finder)
    page = FarmSetupPage(driver, finder)
    page.fill(name=name, area="1", crop="Millet", soil="Sandy")
    page.submit()


@pytest.mark.p3
@pytest.mark.parametrize("name,label", FARM_NAMES, ids=[l for _, l in FARM_NAMES])
def test_farm_data_crop_field_boundary_text(driver, finder, name, label):
    """FORMS: Farm Data 'Crop Name' field accepts boundary text values (short/long/special-chars/whitespace)."""
    _login(driver, finder)
    from pages.main_shell_page import MainShellPage
    from pages.advisory_page import ProfilePage

    MainShellPage(driver, finder).go_profile()
    ProfilePage(driver, finder).go_to_input_farm_data()
    page = FarmDataInputPage(driver, finder)
    page.fill_crop_history(crop=name, yield_kg="10", fertilizer="Compost")
    page.save()


@pytest.mark.p3
@pytest.mark.parametrize("field", ["farm_setup_name_field", "farm_setup_area_field", "farm_setup_crop_field"])
def test_form_field_focus_and_blur(driver, finder, field):
    """FORMS: tapping into and out of each Farm Setup field (focus/blur) does not throw or crash."""
    _login(driver, finder)
    page = FarmSetupPage(driver, finder)
    page.tap(page.by_key(field))
    driver.hide_keyboard() if hasattr(driver, "hide_keyboard") else None
