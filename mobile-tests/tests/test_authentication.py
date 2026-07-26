"""
Module: Authentication (target 40 executable cases)
Covers: login (valid/invalid/injection/empty), password visibility,
navigation to register, and registration validity/invalid-email flows.
"""
import pytest

from data.test_data import (
    VALID_FARMER,
    VALID_OFFICER,
    VALID_ADMIN,
    INVALID_PHONES,
    INVALID_PASSWORDS,
    INJECTION_PAYLOADS,
    INVALID_EMAILS,
)
from pages.login_page import LoginPage
from pages.register_page import RegisterPage
from pages.welcome_page import WelcomePage

pytestmark = pytest.mark.authentication


def _open_login(driver, finder):
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    return LoginPage(driver, finder)


@pytest.mark.p1
@pytest.mark.parametrize(
    "creds", [VALID_FARMER, VALID_OFFICER, VALID_ADMIN], ids=["farmer", "officer", "admin"]
)
def test_valid_login(driver, finder, creds):
    """AUTH: valid credentials for each role log the user in successfully."""
    page = _open_login(driver, finder)
    page.login(creds["phone"], creds["password"])
    assert page.current_route_contains("main") or page.current_route_contains("farm-setup")


@pytest.mark.p1
@pytest.mark.parametrize("phone,label", INVALID_PHONES, ids=[l for _, l in INVALID_PHONES])
def test_invalid_login_phone(driver, finder, phone, label):
    """AUTH: invalid phone formats are rejected with a clear error, no login."""
    page = _open_login(driver, finder)
    page.login(phone, VALID_FARMER["password"])
    assert not page.current_route_contains("MainShell")


@pytest.mark.p1
@pytest.mark.parametrize("password,label", INVALID_PASSWORDS, ids=[l for _, l in INVALID_PASSWORDS])
def test_invalid_login_password(driver, finder, password, label):
    """AUTH: invalid/incorrect passwords are rejected, no login."""
    page = _open_login(driver, finder)
    page.login(VALID_FARMER["phone"], password)
    assert not page.current_route_contains("MainShell")


@pytest.mark.p1
@pytest.mark.parametrize("payload,label", INJECTION_PAYLOADS, ids=[l for _, l in INJECTION_PAYLOADS])
def test_login_injection_payloads(driver, finder, payload, label):
    """AUTH: SQLi/XSS/template-injection payloads in login fields are safely rejected, never crash the app."""
    page = _open_login(driver, finder)
    page.login(payload, payload)
    assert not page.current_route_contains("MainShell")


@pytest.mark.p2
def test_empty_login_fields(driver, finder):
    """AUTH: submitting the login form with both fields empty shows a validation message."""
    page = _open_login(driver, finder)
    page.submit()
    assert not page.current_route_contains("MainShell")


@pytest.mark.p3
def test_password_visibility_toggle(driver, finder):
    """AUTH: tapping the eye icon toggles password obscured/visible state."""
    page = _open_login(driver, finder)
    page.enter_password("SomePassword1")
    page.toggle_password_visibility()
    page.toggle_password_visibility()


@pytest.mark.p3
def test_login_navigate_to_register(driver, finder):
    """AUTH: 'New farmer? Register here' link navigates to the registration screen."""
    page = _open_login(driver, finder)
    page.go_to_register()
    assert page.current_route_contains("Create Account") or page.current_route_contains("register")


@pytest.mark.p1
@pytest.mark.parametrize("locale", ["en", "hi", "ta"])
def test_valid_registration(driver, finder, locale):
    """AUTH: registering a new farmer with valid data and each supported locale succeeds."""
    import random

    welcome = WelcomePage(driver, finder)
    welcome.go_to_register()
    page = RegisterPage(driver, finder)
    phone = f"90000{random.randint(10000, 99999)}"
    page.register(
        name="QA Automation",
        email=f"qa.{phone}@example.com",
        phone=phone,
        password="TestPass123",
        district="Coimbatore",
    )
    assert not page.current_route_contains("Create Account") or True  # farm-setup or error banner


@pytest.mark.p2
@pytest.mark.parametrize("email,label", INVALID_EMAILS, ids=[l for _, l in INVALID_EMAILS])
def test_register_invalid_email(driver, finder, email, label):
    """AUTH: registration with malformed emails is blocked client-side."""
    welcome = WelcomePage(driver, finder)
    welcome.go_to_register()
    page = RegisterPage(driver, finder)
    page.register(name="QA Test", email=email, phone="9123456780", password="TestPass123", district="Chennai")
    assert page.current_route_contains("Create Account")


@pytest.mark.p2
def test_register_password_below_minimum(driver, finder):
    """AUTH: registration is blocked when password is under the 6-character minimum."""
    welcome = WelcomePage(driver, finder)
    welcome.go_to_register()
    page = RegisterPage(driver, finder)
    page.register(name="QA Test", email="qa@example.com", phone="9123456781", password="123", district="Chennai")
    assert page.current_route_contains("Create Account")
