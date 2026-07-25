from pages.base_page import BasePage


class RegisterPage(BasePage):
    NAME_FIELD = "register_name_field"
    EMAIL_FIELD = "register_email_field"
    PHONE_FIELD = "register_phone_field"
    PASSWORD_FIELD = "register_password_field"
    DISTRICT_FIELD = "register_district_field"
    LANGUAGE_SELECTOR = "register_language_selector"
    SUBMIT_BUTTON = "register_submit_button"

    def fill_form(self, name="", email="", phone="", password="", district=""):
        if name:
            self.type_text(self.by_key(self.NAME_FIELD), name)
        if email:
            self.type_text(self.by_key(self.EMAIL_FIELD), email)
        if phone:
            self.type_text(self.by_key(self.PHONE_FIELD), phone)
        if password:
            self.type_text(self.by_key(self.PASSWORD_FIELD), password)
        if district:
            self.type_text(self.by_key(self.DISTRICT_FIELD), district)

    def submit(self):
        self.tap(self.by_key(self.SUBMIT_BUTTON))
        self.wait(2)

    def register(self, **fields):
        self.fill_form(**fields)
        self.submit()
