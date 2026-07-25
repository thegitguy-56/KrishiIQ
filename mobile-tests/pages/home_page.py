from pages.base_page import BasePage


class HomePage(BasePage):
    NOTIFICATIONS_BUTTON = "home_notifications_button"
    LOGOUT_BUTTON = "home_logout_button"
    QUICK_ACTIONS = ["Detect Disease", "Advisory", "Irrigation", "AI Assistant", "My Farms"]

    def open_quick_action(self, label: str):
        assert label in self.QUICK_ACTIONS
        self.tap(self.by_text(label))
        self.wait(1)

    def tap_notifications(self):
        self.tap(self.by_key(self.NOTIFICATIONS_BUTTON))

    def logout(self):
        self.tap(self.by_key(self.LOGOUT_BUTTON))
        self.wait(1)

    def has_weather_card(self) -> bool:
        return "WeatherCard" in self.driver.page_source or "weather" in self.driver.page_source.lower()

    def has_quick_actions_header(self) -> bool:
        return "Quick Actions" in self.driver.page_source

    def pull_to_refresh(self):
        try:
            self.driver.execute_script(
                "mobile: scrollGesture",
                {"direction": "down", "percent": 1.0},
            )
        except Exception:  # noqa: BLE001
            pass
