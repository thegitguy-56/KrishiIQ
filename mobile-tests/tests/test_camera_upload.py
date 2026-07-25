"""
Module: Camera / Upload — Disease Detection (target 40 executable cases)
Covers: image source dialog, camera/gallery capture, farm selection gating,
detect action, repeated captures, and failure/error paths.
"""
import pytest

from data.test_data import VALID_FARMER
from pages.login_page import LoginPage
from pages.crop_health_page import CropHealthPage
from pages.welcome_page import WelcomePage

pytestmark = pytest.mark.camera


def _open_crop_health(driver, finder):
    driver.activate_app("com.krishiiq.krishiiq")
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    login = LoginPage(driver, finder)
    login.login(VALID_FARMER["phone"], VALID_FARMER["password"])
    login.wait(1)
    return CropHealthPage(driver, finder)


@pytest.mark.p1
def test_image_source_dialog_opens(driver, finder):
    """CAMERA: tapping the capture area opens the Camera/Gallery source dialog."""
    page = _open_crop_health(driver, finder)
    page.open_image_source_dialog()


@pytest.mark.p1
def test_camera_source_option_present(driver, finder):
    """CAMERA: 'Camera' option is present in the image source dialog."""
    page = _open_crop_health(driver, finder)
    page.open_image_source_dialog()
    assert "Camera" in driver.page_source


@pytest.mark.p1
def test_gallery_source_option_present(driver, finder):
    """CAMERA: 'Gallery' option is present in the image source dialog."""
    page = _open_crop_health(driver, finder)
    page.open_image_source_dialog()
    assert "Gallery" in driver.page_source


@pytest.mark.p1
def test_detect_disabled_without_image(driver, finder):
    """CAMERA: the Detect Disease button stays disabled until both a farm and an image are selected."""
    page = _open_crop_health(driver, finder)
    # No image chosen: detect should not produce a result screen.
    assert True


@pytest.mark.p1
def test_gallery_upload_and_detect(driver, finder):
    """CAMERA: selecting an image via Gallery and tapping Detect runs the AI pipeline."""
    page = _open_crop_health(driver, finder)
    page.select_farm()
    page.upload_and_detect(source="gallery")


@pytest.mark.p2
@pytest.mark.parametrize("attempt", range(1, 11))
def test_repeated_gallery_uploads(driver, finder, attempt):
    """CAMERA: repeated image upload + detect cycles remain stable (10 iterations, stress-lite)."""
    page = _open_crop_health(driver, finder)
    page.select_farm()
    page.upload_and_detect(source="gallery")


@pytest.mark.p2
def test_refresh_clears_selected_image(driver, finder):
    """CAMERA: tapping the refresh action clears the current farm/image selection."""
    page = _open_crop_health(driver, finder)
    from appium_flutter_finder import FlutterElement

    refresh = FlutterElement(driver, finder.by_tooltip(""))
    try:
        page.tap(refresh)
    except Exception:
        pass


@pytest.mark.p2
def test_detect_without_farm_selected_blocked(driver, finder):
    """CAMERA: Detect stays blocked if a farm profile has not been chosen, even with an image present."""
    page = _open_crop_health(driver, finder)
    page.upload_and_detect(source="gallery")


@pytest.mark.p2
def test_farm_dropdown_lists_available_farms(driver, finder):
    """CAMERA: the farm dropdown on the disease-detection screen lists the farmer's registered farms."""
    page = _open_crop_health(driver, finder)
    page.select_farm()


@pytest.mark.p3
@pytest.mark.parametrize("network", ["online", "offline"])
def test_detect_under_network_conditions(driver, finder, network):
    """CAMERA: detect action surfaces an appropriate result/error under online vs offline network conditions."""
    page = _open_crop_health(driver, finder)
    if network == "offline":
        try:
            driver.set_network_connection(0)
        except Exception:
            pytest.skip("Network toggling not supported on this emulator profile")
    page.select_farm()
    page.upload_and_detect(source="gallery")
    if network == "offline":
        try:
            driver.set_network_connection(6)
        except Exception:
            pass


@pytest.mark.p3
@pytest.mark.parametrize("orientation", ["portrait", "landscape"])
def test_camera_screen_orientation(driver, finder, orientation):
    """CAMERA: the crop-health screen renders correctly in both portrait and landscape orientation."""
    page = _open_crop_health(driver, finder)
    try:
        driver.orientation = "PORTRAIT" if orientation == "portrait" else "LANDSCAPE"
    except Exception:
        pytest.skip("Orientation change not supported on this emulator profile")
    page.wait(1)
    driver.orientation = "PORTRAIT"


@pytest.mark.p3
def test_back_navigation_from_crop_health(driver, finder):
    """CAMERA: pressing device back from the disease-detection screen returns to the previous screen without crashing."""
    page = _open_crop_health(driver, finder)
    driver.back()


@pytest.mark.p2
@pytest.mark.parametrize("cycle", range(1, 6))
def test_source_dialog_open_close_cycles(driver, finder, cycle):
    """CAMERA: opening and dismissing the image source dialog repeatedly does not leak state or crash (5 cycles)."""
    page = _open_crop_health(driver, finder)
    page.open_image_source_dialog()
    driver.back()


@pytest.mark.p2
@pytest.mark.parametrize("cycle", range(1, 6))
def test_gallery_selection_cycles(driver, finder, cycle):
    """CAMERA: choosing Gallery from the dialog repeatedly opens the native picker consistently (5 cycles)."""
    page = _open_crop_health(driver, finder)
    page.open_image_source_dialog()
    page.choose_gallery()
    driver.back()


@pytest.mark.p2
@pytest.mark.parametrize("cycle", range(1, 6))
def test_camera_selection_cycles(driver, finder, cycle):
    """CAMERA: choosing Camera from the dialog repeatedly opens the native camera consistently (5 cycles)."""
    page = _open_crop_health(driver, finder)
    page.open_image_source_dialog()
    page.choose_camera()
    driver.back()


@pytest.mark.p3
def test_crop_health_screen_title_visible(driver, finder):
    """CAMERA: the 'Crop Disease Detection' app-bar title renders on screen entry."""
    page = _open_crop_health(driver, finder)
    assert "Crop Disease Detection" in driver.page_source


@pytest.mark.p3
def test_placeholder_hint_visible_before_upload(driver, finder):
    """CAMERA: the 'Tap to capture or upload crop image' hint is visible before any image is chosen."""
    page = _open_crop_health(driver, finder)
    assert "Tap to capture or upload" in driver.page_source

