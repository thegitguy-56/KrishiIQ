from pages.base_page import BasePage


class LoginPage(BasePage):
    PHONE_FIELD = "login_phone_field"
    PASSWORD_FIELD = "login_password_field"
    PASSWORD_TOGGLE = "login_password_visibility_toggle"
    SUBMIT_BUTTON = "login_submit_button"
    GOTO_REGISTER = "login_goto_register_button"

    def enter_phone(self, phone: str):
        self.type_text(self.by_key(self.PHONE_FIELD), phone)

    def enter_password(self, password: str):
        self.type_text(self.by_key(self.PASSWORD_FIELD), password)

    def toggle_password_visibility(self):
        self.tap(self.by_key(self.PASSWORD_TOGGLE))

    def submit(self):
        self.tap(self.by_key(self.SUBMIT_BUTTON))

    def go_to_register(self):
        self.tap(self.by_key(self.GOTO_REGISTER))

    def login(self, phone: str, password: str):
        self.enter_phone(phone)
        self.enter_password(password)
        self.submit()
        self.wait(2)

    def get_snackbar_text(self) -> str:
        # Flutter SnackBars render as plain text widgets; find_element with
        # a generic text search catches the message shown to the user.
        import re

        source = self.driver.page_source
        match = re.search(r"<text[^>]*>([^<]{3,120})</text>", source)
        return match.group(1) if match else ""
