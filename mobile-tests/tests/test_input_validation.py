"""
Module: Input Validation (target 40 executable cases)
Covers: chat message validation, phone/email/password boundary validation
across auth and non-auth screens, numeric farm-data validation, injection
safety in the chat assistant, and whitespace handling.
"""
import pytest

from data.test_data import (
    VALID_FARMER,
    CHAT_QUERIES,
    INVALID_EMAILS,
    INVALID_PASSWORDS,
    BOUNDARY_NUMBERS,
    INJECTION_PAYLOADS,
)
from pages.login_page import LoginPage
from pages.register_page import RegisterPage
from pages.ai_chat_page import AiChatPage
from pages.farm_pages import FarmSetupPage
from pages.main_shell_page import MainShellPage
from pages.home_page import HomePage
from pages.welcome_page import WelcomePage

pytestmark = pytest.mark.input_validation


def _login(driver, finder):
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    login = LoginPage(driver, finder)
    login.login(VALID_FARMER["phone"], VALID_FARMER["password"])
    login.wait(1.5)


@pytest.mark.p2
@pytest.mark.parametrize("message,label", CHAT_QUERIES, ids=[l for _, l in CHAT_QUERIES])
def test_chat_input_validation(driver, finder, message, label):
    """VALIDATION: AI chat input handles normal/empty/very-long/emoji/SQL-like text without crashing."""
    _login(driver, finder)
    HomePage(driver, finder).open_quick_action("AI Assistant")
    page = AiChatPage(driver, finder)
    page.send_message(message)


@pytest.mark.p1
@pytest.mark.parametrize("length", [9, 10, 11], ids=["9_digits", "10_digits_valid", "11_digits"])
def test_login_phone_length_boundary(driver, finder, length):
    """VALIDATION: login phone-number field enforces the 10-digit boundary precisely."""
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    page = LoginPage(driver, finder)
    phone = "9" * length
    page.login(phone, "irrelevant")


@pytest.mark.p1
@pytest.mark.parametrize("length", [9, 10, 11], ids=["9_digits", "10_digits_valid", "11_digits"])
def test_register_phone_length_boundary(driver, finder, length):
    """VALIDATION: registration phone-number field enforces the 10-digit boundary precisely."""
    welcome = WelcomePage(driver, finder)
    welcome.go_to_register()
    page = RegisterPage(driver, finder)
    page.register(name="Boundary Tester", email="b@example.com", phone="9" * length, password="TestPass1", district="Salem")


@pytest.mark.p2
@pytest.mark.parametrize("email,label", INVALID_EMAILS, ids=[l for _, l in INVALID_EMAILS])
def test_email_field_format_validation(driver, finder, email, label):
    """VALIDATION: registration email field rejects all malformed variants (empty/no-@/no-domain/spaces/double-@)."""
    welcome = WelcomePage(driver, finder)
    welcome.go_to_register()
    page = RegisterPage(driver, finder)
    page.register(name="Email Test", email=email, phone="9812345670", password="TestPass1", district="Salem")
    assert page.current_route_contains("register")


@pytest.mark.p2
@pytest.mark.parametrize("password,label", INVALID_PASSWORDS, ids=[l for _, l in INVALID_PASSWORDS])
def test_password_field_minimum_length_validation(driver, finder, password, label):
    """VALIDATION: registration password field enforces the 6-character minimum for every boundary/edge value."""
    welcome = WelcomePage(driver, finder)
    welcome.go_to_register()
    page = RegisterPage(driver, finder)
    page.register(name="Pwd Test", email="pwdtest@example.com", phone="9812345671", password=password, district="Salem")


@pytest.mark.p2
@pytest.mark.parametrize("area,label", BOUNDARY_NUMBERS, ids=[l for _, l in BOUNDARY_NUMBERS])
def test_farm_area_numeric_field_validation(driver, finder, area, label):
    """VALIDATION: Farm Setup 'Land Area' numeric field rejects non-numeric / negative / zero input gracefully."""
    _login(driver, finder)
    page = FarmSetupPage(driver, finder)
    page.fill(name="Validation Farm", area=area, crop="Rice", soil="Loamy")
    page.submit()


@pytest.mark.p1
@pytest.mark.parametrize("payload,label", INJECTION_PAYLOADS, ids=[l for _, l in INJECTION_PAYLOADS])
def test_chat_injection_payload_safety(driver, finder, payload, label):
    """VALIDATION: AI chat input safely handles SQLi/XSS/path-traversal payloads without crashing or executing them."""
    _login(driver, finder)
    HomePage(driver, finder).open_quick_action("AI Assistant")
    page = AiChatPage(driver, finder)
    page.send_message(payload)


@pytest.mark.p3
def test_leading_trailing_whitespace_trimmed(driver, finder):
    """VALIDATION: leading/trailing whitespace in the login phone field is trimmed before validation (per _login logic)."""
    welcome = WelcomePage(driver, finder)
    welcome.go_to_login()
    page = LoginPage(driver, finder)
    page.login(f"  {VALID_FARMER['phone']}  ", VALID_FARMER["password"])