from pages.base_page import BasePage


class WelcomePage(BasePage):
    def go_to_register(self):
        self.tap(self.by_text("Register"))

    def go_to_login(self):
        self.tap(self.by_text("Sign In"))
