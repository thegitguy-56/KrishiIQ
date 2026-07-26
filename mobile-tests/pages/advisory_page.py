from pages.base_page import BasePage


class AdvisoryPage(BasePage):
    def refresh(self):
        # AppBar refresh IconButton has no unique text, but is the only
        # IconButton in the AppBar actions on this screen.
        from appium_flutter_finder import FlutterElement

        el = FlutterElement(self.driver, self.finder.by_tooltip("Refresh"))
        self.tap(el)

    def has_any_advisory_card(self) -> bool:
        return self.is_text_present("Personalized Advisory", timeout=4)


class ProfilePage(BasePage):
    INPUT_FARM_DATA_TILE = "Input Farm Data"
    SIGN_OUT_TILE = "Sign Out"

    def go_to_input_farm_data(self):
        self.tap(self.by_text(self.INPUT_FARM_DATA_TILE))

    def sign_out(self):
        self.tap(self.by_text(self.SIGN_OUT_TILE))
        self.wait(1.5)

    def set_language(self, label: str):
        assert label in ("English", "हिंदी", "தமிழ்")
        self.tap(self.by_text(label))
