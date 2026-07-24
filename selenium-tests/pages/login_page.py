"""
LoginPage — Page Object for /login
"""
from selenium.webdriver.common.by import By
from .base_page import BasePage
import config


class LoginPage(BasePage):
    # ── Locators ──────────────────────────────────────────────────────────────
    PHONE_INPUT    = (By.CSS_SELECTOR, "input[type='tel']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[type='password']")
    SUBMIT_BTN     = (By.CSS_SELECTOR, "button[type='submit']")
    LOGO_TEXT      = (By.XPATH, "//div[contains(text(),'KrishiIQ')]")
    PORTAL_LABEL   = (By.XPATH, "//div[contains(text(),'Officer & Admin Portal')]")
    FARMER_NOTICE  = (By.XPATH, "//span[contains(text(),'Farmers: use the mobile app')]")
    DEMO_TEXT      = (By.XPATH, "//*[contains(text(),'Demo:')]")
    TOAST_SUCCESS  = (By.CSS_SELECTOR, "[data-testid='toast'], [class*='toast']")

    # ── Actions ───────────────────────────────────────────────────────────────

    def load(self) -> "LoginPage":
        self.open(config.ROUTES["login"])
        self.find_visible(*self.PHONE_INPUT)
        return self

    def enter_phone(self, phone: str) -> "LoginPage":
        self.type_text(*self.PHONE_INPUT, phone)
        return self

    def enter_password(self, password: str) -> "LoginPage":
        self.type_text(*self.PASSWORD_INPUT, password)
        return self

    def click_submit(self) -> "LoginPage":
        self.click(*self.SUBMIT_BTN)
        return self

    def login(self, phone: str, password: str) -> "LoginPage":
        self.enter_phone(phone)
        self.enter_password(password)
        self.click_submit()
        return self

    def login_as_officer(self) -> "LoginPage":
        return self.login(config.OFFICER_PHONE, config.OFFICER_PASSWORD)

    def login_as_admin(self) -> "LoginPage":
        return self.login(config.ADMIN_PHONE, config.ADMIN_PASSWORD)

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_phone_value(self) -> str:
        return self.get_attribute(*self.PHONE_INPUT, "value")

    def get_password_value(self) -> str:
        return self.get_attribute(*self.PASSWORD_INPUT, "value")

    def get_submit_text(self) -> str:
        return self.get_text(*self.SUBMIT_BTN)

    def is_submit_disabled(self) -> bool:
        return not self.is_element_enabled(*self.SUBMIT_BTN)

    def is_logo_visible(self) -> bool:
        return self.is_visible(*self.LOGO_TEXT)

    def is_farmer_notice_visible(self) -> bool:
        return self.is_visible(*self.FARMER_NOTICE)

    def get_page_title(self) -> str:
        return self.get_title()

    def is_on_login_page(self) -> bool:
        return "login" in self.get_current_url()

    def get_phone_placeholder(self) -> str:
        return self.get_attribute(*self.PHONE_INPUT, "placeholder")

    def get_password_type(self) -> str:
        return self.get_attribute(*self.PASSWORD_INPUT, "type")

    def is_phone_required(self) -> bool:
        return self.get_attribute(*self.PHONE_INPUT, "required") is not None

    def is_password_required(self) -> bool:
        return self.get_attribute(*self.PASSWORD_INPUT, "required") is not None

    def clear_phone(self) -> "LoginPage":
        self.clear_field(*self.PHONE_INPUT)
        return self

    def clear_password(self) -> "LoginPage":
        self.clear_field(*self.PASSWORD_INPUT)
        return self

    def is_demo_credentials_visible(self) -> bool:
        return self.is_present(*self.DEMO_TEXT)

    def get_background_style(self) -> str:
        body = self.driver.find_element(By.TAG_NAME, "div")
        return body.get_attribute("class") or ""
