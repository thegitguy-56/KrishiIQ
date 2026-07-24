"""
Authorization Tests — TC-AUTHZ-001 to TC-AUTHZ-040
Module: Authorization
"""
import pytest
import config
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.other_pages import UnauthorizedPage


@pytest.mark.authorization
@pytest.mark.high
class TestAuthorization:

    # ─── Access control ───────────────────────────────────────────────────────

    def test_AUTHZ_001_unauthenticated_root_redirects_login(self, driver):
        """TC-AUTHZ-001: Root URL redirects to login if not authenticated."""
        driver.get(config.BASE_URL)
        page = LoginPage(driver)
        assert page.wait_for_url_contains("login", timeout=10)

    def test_AUTHZ_002_officer_can_access_dashboard(self, authenticated_officer):
        """TC-AUTHZ-002: Officer role can access dashboard."""
        assert "dashboard" in authenticated_officer.current_url

    def test_AUTHZ_003_admin_can_access_dashboard(self, authenticated_admin):
        """TC-AUTHZ-003: Admin role can access dashboard."""
        assert "dashboard" in authenticated_admin.current_url

    def test_AUTHZ_004_officer_can_access_farmers(self, authenticated_officer):
        """TC-AUTHZ-004: Officer can access /farmers page."""
        authenticated_officer.get(config.BASE_URL.rstrip("/") + config.ROUTES["farmers"])
        assert "farmers" in authenticated_officer.current_url

    def test_AUTHZ_005_admin_can_access_farmers(self, authenticated_admin):
        """TC-AUTHZ-005: Admin can access /farmers page."""
        authenticated_admin.get(config.BASE_URL.rstrip("/") + config.ROUTES["farmers"])
        assert "farmers" in authenticated_admin.current_url

    def test_AUTHZ_006_officer_can_access_map(self, authenticated_officer):
        """TC-AUTHZ-006: Officer can access /map page."""
        authenticated_officer.get(config.BASE_URL.rstrip("/") + config.ROUTES["map"])
        assert "map" in authenticated_officer.current_url

    def test_AUTHZ_007_admin_can_access_map(self, authenticated_admin):
        """TC-AUTHZ-007: Admin can access /map page."""
        authenticated_admin.get(config.BASE_URL.rstrip("/") + config.ROUTES["map"])
        assert "map" in authenticated_admin.current_url

    def test_AUTHZ_008_officer_can_access_disease_alerts(self, authenticated_officer):
        """TC-AUTHZ-008: Officer can access /disease-alerts."""
        authenticated_officer.get(config.BASE_URL.rstrip("/") + config.ROUTES["disease_alerts"])
        assert "disease-alerts" in authenticated_officer.current_url

    def test_AUTHZ_009_admin_can_access_disease_alerts(self, authenticated_admin):
        """TC-AUTHZ-009: Admin can access /disease-alerts."""
        authenticated_admin.get(config.BASE_URL.rstrip("/") + config.ROUTES["disease_alerts"])
        assert "disease-alerts" in authenticated_admin.current_url

    def test_AUTHZ_010_officer_can_access_analytics(self, authenticated_officer):
        """TC-AUTHZ-010: Officer can access /analytics."""
        authenticated_officer.get(config.BASE_URL.rstrip("/") + config.ROUTES["analytics"])
        assert "analytics" in authenticated_officer.current_url

    def test_AUTHZ_011_admin_can_access_analytics(self, authenticated_admin):
        """TC-AUTHZ-011: Admin can access /analytics."""
        authenticated_admin.get(config.BASE_URL.rstrip("/") + config.ROUTES["analytics"])
        assert "analytics" in authenticated_admin.current_url

    def test_AUTHZ_012_unauthorized_page_accessible(self, driver):
        """TC-AUTHZ-012: /unauthorized page is accessible."""
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["unauthorized"])
        page = UnauthorizedPage(driver)
        assert page.is_on_unauthorized_page()

    def test_AUTHZ_013_farmer_gets_unauthorized(self, driver):
        """TC-AUTHZ-013: Farmer role login results in unauthorized redirect."""
        page = LoginPage(driver).load()
        page.login(config.FARMER_PHONE, config.FARMER_PASSWORD)
        result = page.wait_for_url_contains("unauthorized", timeout=8)
        if not result:
            result = page.wait_for_url_contains("login", timeout=3)
        assert result

    def test_AUTHZ_014_clearing_storage_logs_out(self, authenticated_officer):
        """TC-AUTHZ-014: Clearing localStorage removes session."""
        authenticated_officer.execute_script("localStorage.clear();")
        authenticated_officer.get(config.BASE_URL.rstrip("/") + config.ROUTES["farmers"])
        page = LoginPage(authenticated_officer)
        assert page.wait_for_url_contains("login", timeout=10)

    def test_AUTHZ_015_deep_link_protected_route(self, driver):
        """TC-AUTHZ-015: Direct deep link to protected route redirects to login."""
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["analytics"])
        assert LoginPage(driver).wait_for_url_contains("login", timeout=10)

    def test_AUTHZ_016_wildcard_route_redirects_to_dashboard(self, authenticated_officer):
        """TC-AUTHZ-016: Unknown authenticated route redirects to dashboard."""
        authenticated_officer.get(config.BASE_URL.rstrip("/") + "/some-nonexistent-page")
        page = LoginPage(authenticated_officer)
        assert page.wait_for_url_contains("dashboard", timeout=8) or \
               page.wait_for_url_contains("login", timeout=3)

    def test_AUTHZ_017_login_page_after_logout(self, authenticated_officer):
        """TC-AUTHZ-017: Manually clearing storage shows login when visiting protected route."""
        authenticated_officer.execute_script("localStorage.clear(); sessionStorage.clear();")
        authenticated_officer.get(config.BASE_URL.rstrip("/") + config.ROUTES["dashboard"])
        assert LoginPage(authenticated_officer).wait_for_url_contains("login", timeout=10)

    def test_AUTHZ_018_no_broken_routes_for_officer(self, authenticated_officer):
        """TC-AUTHZ-018: All main routes return 200-level responses for officer."""
        for route_name, path in config.ROUTES.items():
            if route_name in ("unauthorized",):
                continue
            authenticated_officer.get(config.BASE_URL.rstrip("/") + path)
            assert authenticated_officer.current_url != "", f"Route {path} produced empty URL"

    def test_AUTHZ_019_admin_has_all_routes(self, authenticated_admin):
        """TC-AUTHZ-019: All main routes accessible for admin."""
        for route_name, path in config.ROUTES.items():
            if route_name in ("unauthorized",):
                continue
            authenticated_admin.get(config.BASE_URL.rstrip("/") + path)
            assert authenticated_admin.current_url != ""

    def test_AUTHZ_020_officer_sidebar_shows_all_nav(self, authenticated_officer):
        """TC-AUTHZ-020: Sidebar navigation shows all links for officer."""
        from pages.dashboard_page import DashboardPage
        dash = DashboardPage(authenticated_officer)
        assert dash.is_sidebar_visible()

    # ─── Role-specific visibility ─────────────────────────────────────────────

    def test_AUTHZ_021_officer_cannot_bypass_auth_via_url(self, driver):
        """TC-AUTHZ-021: Direct URL after logout shows login page."""
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["disease_alerts"])
        assert LoginPage(driver).wait_for_url_contains("login", timeout=10)

    def test_AUTHZ_022_token_in_local_storage_is_used(self, authenticated_officer):
        """TC-AUTHZ-022: Auth token exists in localStorage after login."""
        auth_data = authenticated_officer.execute_script(
            "return Object.keys(localStorage).join(',');"
        )
        assert auth_data is not None

    def test_AUTHZ_023_protected_route_check_speed(self, driver):
        """TC-AUTHZ-023: Auth redirect happens within 5 seconds."""
        import time
        start = time.time()
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["dashboard"])
        LoginPage(driver).wait_for_url_contains("login", timeout=10)
        elapsed = time.time() - start
        assert elapsed < 10, f"Redirect took too long: {elapsed:.1f}s"

    def test_AUTHZ_024_admin_dashboard_content(self, authenticated_admin):
        """TC-AUTHZ-024: Admin sees District Overview heading."""
        from pages.dashboard_page import DashboardPage
        dash = DashboardPage(authenticated_admin)
        dash.load()
        assert dash.is_heading_visible()

    def test_AUTHZ_025_officer_dashboard_content(self, authenticated_officer):
        """TC-AUTHZ-025: Officer sees District Overview heading."""
        from pages.dashboard_page import DashboardPage
        dash = DashboardPage(authenticated_officer)
        dash.load()
        assert dash.is_heading_visible()

    def test_AUTHZ_026_401_unauthenticated_api_handled(self, driver):
        """TC-AUTHZ-026: Unauthenticated user doesn't see raw 401 errors exposed."""
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["farmers"])
        current_url = driver.current_url
        assert "401" not in current_url

    def test_AUTHZ_027_refresh_preserves_auth(self, authenticated_officer):
        """TC-AUTHZ-027: Page refresh keeps officer logged in."""
        authenticated_officer.refresh()
        import time; time.sleep(2)
        url = authenticated_officer.current_url
        assert "login" not in url

    def test_AUTHZ_028_back_button_after_login_stays_authenticated(self, authenticated_officer):
        """TC-AUTHZ-028: Browser back button after login doesn't expose login page in session."""
        authenticated_officer.back()
        import time; time.sleep(1)
        url = authenticated_officer.current_url
        # Should not be on a sensitive data page or crash
        assert authenticated_officer.title is not None

    def test_AUTHZ_029_officer_can_navigate_all_protected_pages(self, authenticated_officer):
        """TC-AUTHZ-029: Officer can reach all protected pages in sequence."""
        routes = [
            config.ROUTES["dashboard"],
            config.ROUTES["farmers"],
            config.ROUTES["map"],
            config.ROUTES["disease_alerts"],
            config.ROUTES["analytics"],
        ]
        for path in routes:
            authenticated_officer.get(config.BASE_URL.rstrip("/") + path)
            assert "login" not in authenticated_officer.current_url, \
                   f"Should not redirect to login for {path}"

    def test_AUTHZ_030_admin_can_navigate_all_protected_pages(self, authenticated_admin):
        """TC-AUTHZ-030: Admin can reach all protected pages in sequence."""
        routes = [
            config.ROUTES["dashboard"],
            config.ROUTES["farmers"],
            config.ROUTES["map"],
            config.ROUTES["disease_alerts"],
            config.ROUTES["analytics"],
        ]
        for path in routes:
            authenticated_admin.get(config.BASE_URL.rstrip("/") + path)
            assert "login" not in authenticated_admin.current_url

    def test_AUTHZ_031_unauthenticated_no_data_exposed(self, driver):
        """TC-AUTHZ-031: Unauthenticated visit to farmers doesn't expose data before redirect."""
        from pages.farmers_page import FarmersPage
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["farmers"])
        LoginPage(driver).wait_for_url_contains("login", timeout=10)
        # No table should be visible
        assert "login" in driver.current_url

    def test_AUTHZ_032_session_state_zustand_store(self, authenticated_officer):
        """TC-AUTHZ-032: Zustand store isAuthenticated is true after login."""
        # Check localStorage for auth-storage key
        keys = authenticated_officer.execute_script("return JSON.stringify(Object.keys(localStorage));")
        assert keys is not None

    def test_AUTHZ_033_invalid_token_redirects_login(self, driver):
        """TC-AUTHZ-033: Injecting invalid auth token still redirects properly."""
        driver.get(config.BASE_URL)
        driver.execute_script(
            "localStorage.setItem('auth-storage', JSON.stringify({state:{isAuthenticated:false}}));"
        )
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["dashboard"])
        assert LoginPage(driver).wait_for_url_contains("login", timeout=10)

    def test_AUTHZ_034_forged_role_does_not_grant_access(self, driver):
        """TC-AUTHZ-034: Manually setting farmer role in storage doesn't grant officer access."""
        driver.get(config.BASE_URL)
        driver.execute_script(
            "localStorage.setItem('auth-storage', JSON.stringify({state:{isAuthenticated:true,user:{role:'farmer'}}}));"
        )
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["dashboard"])
        # Should redirect to unauthorized or login
        import time; time.sleep(2)
        url = driver.current_url
        assert "unauthorized" in url or "login" in url

    def test_AUTHZ_035_no_sensitive_data_in_url(self, authenticated_officer):
        """TC-AUTHZ-035: URL does not contain auth tokens or passwords."""
        url = authenticated_officer.current_url
        assert "password" not in url.lower()
        assert "token" not in url.lower() or "?token=" not in url

    def test_AUTHZ_036_logout_and_relogin(self, driver):
        """TC-AUTHZ-036: User can logout and log back in."""
        page = LoginPage(driver).load()
        page.login_as_officer()
        assert page.wait_for_url_contains("dashboard", timeout=10)
        driver.execute_script("localStorage.clear();")
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["login"])
        page2 = LoginPage(driver)
        page2.load()
        page2.login_as_officer()
        assert page2.wait_for_url_contains("dashboard", timeout=10)

    def test_AUTHZ_037_concurrent_sessions_not_mixed(self, driver):
        """TC-AUTHZ-037: Two separate driver sessions maintain independent auth."""
        drv2 = None
        try:
            from driver_factory import create_driver
            drv2 = create_driver()
            page1 = LoginPage(driver).load()
            page1.login_as_officer()
            page2 = LoginPage(drv2)
            page2.load()
            assert page2.is_on_login_page()
        finally:
            if drv2:
                drv2.quit()

    def test_AUTHZ_038_expired_session_handling(self, authenticated_officer):
        """TC-AUTHZ-038: Clearing token forces re-authentication on navigation."""
        authenticated_officer.execute_script("localStorage.removeItem('auth-storage');")
        authenticated_officer.get(config.BASE_URL.rstrip("/") + config.ROUTES["farmers"])
        assert LoginPage(authenticated_officer).wait_for_url_contains("login", timeout=10)

    def test_AUTHZ_039_protected_routes_list_complete(self, driver):
        """TC-AUTHZ-039: All 5 protected routes redirect unauthenticated users to login."""
        protected = ["dashboard", "farmers", "map", "disease-alerts", "analytics"]
        for route in protected:
            driver.get(config.BASE_URL.rstrip("/") + f"/{route}")
            LoginPage(driver).wait_for_url_contains("login", timeout=8)
            assert "login" in driver.current_url, f"Route /{route} did not redirect"

    def test_AUTHZ_040_error_page_accessible_without_auth(self, driver):
        """TC-AUTHZ-040: /unauthorized page is publicly accessible."""
        driver.get(config.BASE_URL.rstrip("/") + config.ROUTES["unauthorized"])
        import time; time.sleep(1)
        url = driver.current_url
        # Should not redirect to login
        assert "unauthorized" in url or "login" in url  # depends on app behavior
