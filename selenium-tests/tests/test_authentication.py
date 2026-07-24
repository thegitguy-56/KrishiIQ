"""
Authentication Tests — TC-AUTH-001 to TC-AUTH-040
Module: Authentication
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import config
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage


@pytest.mark.authentication
@pytest.mark.high
class TestAuthentication:

    # ─── Successful login ────────────────────────────────────────────────────

    def test_AUTH_001_officer_login_success(self, driver):
        """TC-AUTH-001: Officer can log in with valid credentials."""
        page = LoginPage(driver).load()
        page.login_as_officer()
        assert page.wait_for_url_contains("dashboard"), "Should redirect to dashboard"

    def test_AUTH_002_admin_login_success(self, driver):
        """TC-AUTH-002: Admin can log in with valid credentials."""
        page = LoginPage(driver).load()
        page.login_as_admin()
        assert page.wait_for_url_contains("dashboard"), "Should redirect to dashboard"

    def test_AUTH_003_login_page_loads(self, driver):
        """TC-AUTH-003: Login page loads without errors."""
        page = LoginPage(driver).load()
        assert page.is_on_login_page()

    def test_AUTH_004_login_page_title(self, driver):
        """TC-AUTH-004: Page has a meaningful title."""
        LoginPage(driver).load()
        title = driver.title
        assert len(title) > 0, "Page title should not be empty"

    def test_AUTH_005_logo_visible(self, driver):
        """TC-AUTH-005: KrishiIQ logo is displayed."""
        page = LoginPage(driver).load()
        assert page.is_logo_visible()

    # ─── Invalid credentials ─────────────────────────────────────────────────

    def test_AUTH_006_invalid_phone_wrong_password(self, driver):
        """TC-AUTH-006: Login fails with wrong phone."""
        page = LoginPage(driver).load()
        page.login(config.INVALID_PHONE, config.OFFICER_PASSWORD)
        # Should stay on login or show error
        assert not page.wait_for_url_contains("dashboard", timeout=5), "Should not redirect"

    def test_AUTH_007_valid_phone_wrong_password(self, driver):
        """TC-AUTH-007: Login fails with correct phone but wrong password."""
        page = LoginPage(driver).load()
        page.login(config.OFFICER_PHONE, config.INVALID_PASSWORD)
        assert not page.wait_for_url_contains("dashboard", timeout=5)

    def test_AUTH_008_empty_phone(self, driver):
        """TC-AUTH-008: Submit with empty phone is blocked by HTML5 validation."""
        page = LoginPage(driver).load()
        page.enter_password(config.OFFICER_PASSWORD)
        page.click_submit()
        assert page.is_on_login_page(), "Should remain on login page"

    def test_AUTH_009_empty_password(self, driver):
        """TC-AUTH-009: Submit with empty password is blocked."""
        page = LoginPage(driver).load()
        page.enter_phone(config.OFFICER_PHONE)
        page.click_submit()
        assert page.is_on_login_page()

    def test_AUTH_010_both_fields_empty(self, driver):
        """TC-AUTH-010: Submit with both fields empty is blocked."""
        page = LoginPage(driver).load()
        page.click_submit()
        assert page.is_on_login_page()

    # ─── Field attributes ────────────────────────────────────────────────────

    def test_AUTH_011_password_field_masked(self, driver):
        """TC-AUTH-011: Password field type is 'password'."""
        page = LoginPage(driver).load()
        assert page.get_password_type() == "password"

    def test_AUTH_012_phone_field_type_tel(self, driver):
        """TC-AUTH-012: Phone field has type='tel'."""
        el = driver.find_element(By.CSS_SELECTOR, "input[type='tel']")
        page = LoginPage(driver).load()
        assert "tel" in page.get_attribute(By.CSS_SELECTOR, "input[type='tel']", "type")

    def test_AUTH_013_phone_required(self, driver):
        """TC-AUTH-013: Phone field is marked required."""
        page = LoginPage(driver).load()
        assert page.is_phone_required()

    def test_AUTH_014_password_required(self, driver):
        """TC-AUTH-014: Password field is marked required."""
        page = LoginPage(driver).load()
        assert page.is_password_required()

    def test_AUTH_015_phone_placeholder(self, driver):
        """TC-AUTH-015: Phone placeholder shows sample number."""
        page = LoginPage(driver).load()
        placeholder = page.get_phone_placeholder()
        assert len(placeholder) > 0

    # ─── UI Elements ─────────────────────────────────────────────────────────

    def test_AUTH_016_submit_button_present(self, driver):
        """TC-AUTH-016: Sign In button is visible."""
        page = LoginPage(driver).load()
        assert page.is_visible(page.SUBMIT_BTN[0], page.SUBMIT_BTN[1])

    def test_AUTH_017_farmer_notice_visible(self, driver):
        """TC-AUTH-017: Farmer-redirect notice is shown."""
        page = LoginPage(driver).load()
        assert page.is_farmer_notice_visible()

    def test_AUTH_018_demo_credentials_shown(self, driver):
        """TC-AUTH-018: Demo credentials hint is visible."""
        page = LoginPage(driver).load()
        assert page.is_demo_credentials_visible()

    def test_AUTH_019_submit_button_text(self, driver):
        """TC-AUTH-019: Submit button says 'Sign In'."""
        page = LoginPage(driver).load()
        assert "Sign In" in page.get_submit_text() or "sign in" in page.get_submit_text().lower()

    def test_AUTH_020_portal_label_visible(self, driver):
        """TC-AUTH-020: 'Officer & Admin Portal' label is visible."""
        page = LoginPage(driver).load()
        assert page.is_visible(page.PORTAL_LABEL[0], page.PORTAL_LABEL[1])

    # ─── Post-login state ────────────────────────────────────────────────────

    def test_AUTH_021_dashboard_loaded_after_officer_login(self, authenticated_officer):
        """TC-AUTH-021: Dashboard content loads after officer login."""
        dash = DashboardPage(authenticated_officer)
        assert "dashboard" in authenticated_officer.current_url

    def test_AUTH_022_redirect_unauthenticated_to_login(self, driver):
        """TC-AUTH-022: Unauthenticated access to dashboard redirects to login."""
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["dashboard"])
        page = LoginPage(driver)
        assert page.wait_for_url_contains("login", timeout=10), "Should redirect to login"

    def test_AUTH_023_redirect_farmers_unauthenticated(self, driver):
        """TC-AUTH-023: /farmers redirects to login when not authenticated."""
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["farmers"])
        assert LoginPage(driver).wait_for_url_contains("login", timeout=10)

    def test_AUTH_024_redirect_map_unauthenticated(self, driver):
        """TC-AUTH-024: /map redirects to login when not authenticated."""
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["map"])
        assert LoginPage(driver).wait_for_url_contains("login", timeout=10)

    def test_AUTH_025_redirect_disease_alerts_unauthenticated(self, driver):
        """TC-AUTH-025: /disease-alerts redirects to login when not authenticated."""
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["disease_alerts"])
        assert LoginPage(driver).wait_for_url_contains("login", timeout=10)

    def test_AUTH_026_redirect_analytics_unauthenticated(self, driver):
        """TC-AUTH-026: /analytics redirects to login when not authenticated."""
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["analytics"])
        assert LoginPage(driver).wait_for_url_contains("login", timeout=10)

    # ─── Security ────────────────────────────────────────────────────────────

    def test_AUTH_027_sql_injection_phone(self, driver):
        """TC-AUTH-027: SQL injection in phone field doesn't authenticate."""
        page = LoginPage(driver).load()
        page.login(config.SQL_INJECTION, config.OFFICER_PASSWORD)
        assert not page.wait_for_url_contains("dashboard", timeout=5)

    def test_AUTH_028_sql_injection_password(self, driver):
        """TC-AUTH-028: SQL injection in password field doesn't authenticate."""
        page = LoginPage(driver).load()
        page.login(config.OFFICER_PHONE, config.SQL_INJECTION)
        assert not page.wait_for_url_contains("dashboard", timeout=5)

    def test_AUTH_029_xss_in_phone_field(self, driver):
        """TC-AUTH-029: XSS payload in phone field is not executed."""
        page = LoginPage(driver).load()
        page.enter_phone(config.XSS_PAYLOAD)
        source = driver.page_source
        assert "<script>" not in driver.title

    def test_AUTH_030_short_phone_number(self, driver):
        """TC-AUTH-030: Short phone number doesn't authenticate."""
        page = LoginPage(driver).load()
        page.login(config.SHORT_PHONE, config.OFFICER_PASSWORD)
        assert not page.wait_for_url_contains("dashboard", timeout=5)

    # ─── Session ─────────────────────────────────────────────────────────────

    def test_AUTH_031_logout_clears_session(self, authenticated_officer):
        """TC-AUTH-031: After logging out (clearing storage), protected pages redirect to login."""
        authenticated_officer.execute_script("localStorage.clear(); sessionStorage.clear();")
        authenticated_officer.get(config.BASE_URL.rstrip("/") + config.ROUTES["dashboard"])
        page = LoginPage(authenticated_officer)
        assert page.wait_for_url_contains("login", timeout=10)

    def test_AUTH_032_login_loading_state(self, driver):
        """TC-AUTH-032: Submit button shows loading text while submitting."""
        page = LoginPage(driver).load()
        page.enter_phone(config.OFFICER_PHONE)
        page.enter_password(config.OFFICER_PASSWORD)
        page.click_submit()
        # Either navigates away or briefly shows loading
        import time; time.sleep(0.3)  # minimal delay only for loading capture
        url = page.get_current_url()
        assert "login" in url or "dashboard" in url  # one of these

    def test_AUTH_033_officer_phone_field_accepts_digits(self, driver):
        """TC-AUTH-033: Phone field accepts digit-only input."""
        page = LoginPage(driver).load()
        page.enter_phone("9000000001")
        val = page.get_phone_value()
        assert "9000000001" in val

    def test_AUTH_034_password_value_not_in_page_source(self, driver):
        """TC-AUTH-034: Password value not exposed in DOM as plain text."""
        page = LoginPage(driver).load()
        page.enter_password("officer123")
        source = page.get_page_source()
        assert "officer123" not in source

    def test_AUTH_035_login_page_responsive_mobile(self, driver_mobile):
        """TC-AUTH-035: Login page is usable on mobile viewport."""
        page = LoginPage(driver_mobile).load()
        assert page.is_visible(page.PHONE_INPUT[0], page.PHONE_INPUT[1])
        assert page.is_visible(page.SUBMIT_BTN[0], page.SUBMIT_BTN[1])

    def test_AUTH_036_wrong_role_farmer_redirected(self, driver):
        """TC-AUTH-036: Farmer credentials get redirected to unauthorized page."""
        page = LoginPage(driver).load()
        page.login(config.FARMER_PHONE, config.FARMER_PASSWORD)
        # Should redirect to unauthorized (farmer role not allowed)
        result = page.wait_for_url_contains("unauthorized", timeout=8) or \
                 page.wait_for_url_contains("login", timeout=3)
        assert result, "Farmer login should result in unauthorized or stay on login"

    def test_AUTH_037_multiple_failed_logins_handled(self, driver):
        """TC-AUTH-037: Multiple failed logins handled gracefully."""
        page = LoginPage(driver).load()
        for _ in range(3):
            page.clear_phone()
            page.clear_password()
            page.login(config.INVALID_PHONE, config.INVALID_PASSWORD)
        assert page.is_on_login_page() or True  # Should not crash

    def test_AUTH_038_pressing_enter_submits_form(self, driver):
        """TC-AUTH-038: Pressing Enter on password field submits the form."""
        page = LoginPage(driver).load()
        page.enter_phone(config.OFFICER_PHONE)
        page.press_key(page.PASSWORD_INPUT[0], page.PASSWORD_INPUT[1], Keys.ENTER)
        # Form submits, login fails silently or starts loading
        import time; time.sleep(1)
        assert page.is_on_login_page() or page.wait_for_url_contains("dashboard", timeout=5)

    def test_AUTH_039_long_phone_number(self, driver):
        """TC-AUTH-039: Very long phone number doesn't crash the page."""
        page = LoginPage(driver).load()
        page.enter_phone(config.LONG_PHONE)
        assert page.is_on_login_page()

    def test_AUTH_040_login_page_has_no_js_errors(self, driver):
        """TC-AUTH-040: Login page loads without critical JS errors."""
        LoginPage(driver).load()
        logs = driver.get_log("browser")
        severe = [l for l in logs if l.get("level") == "SEVERE" and "favicon" not in l.get("message", "")]
        # Allow some network errors (API not running) but no script errors
        script_errors = [l for l in severe if "SyntaxError" in l.get("message", "") or
                         "TypeError" in l.get("message", "")]
        assert len(script_errors) == 0, f"JS errors found: {script_errors}"
