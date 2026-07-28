from pages.base_page import BasePage


class HomePage(BasePage):
    NOTIFICATIONS_BUTTON = "home_notifications_button"
    LOGOUT_BUTTON = "home_logout_button"
    QUICK_ACTIONS = ["Detect Disease", "Advisory", "Irrigation", "AI Assistant", "My Farms"]
    _QUICK_ACTION_KEYS = {
        "Detect Disease": "quick_action_detect_disease",
        "Advisory": "quick_action_advisory",
        "Irrigation": "quick_action_irrigation",
        "AI Assistant": "quick_action_ai_assistant",
        "My Farms": "quick_action_my_farms",
    }

    def open_quick_action(self, label: str):
        assert label in self.QUICK_ACTIONS
        self.tap(self.by_key(self._QUICK_ACTION_KEYS[label]))
        self.wait(1)

    def tap_notifications(self):
        self.tap(self.by_key(self.NOTIFICATIONS_BUTTON))

    def logout(self):
        self.tap(self.by_key(self.LOGOUT_BUTTON))
        self.wait(1)

    def has_weather_card(self) -> bool:
        return self.is_present(self.by_type("WeatherCard"), timeout=4)

    def has_quick_actions_header(self) -> bool:
        return self.is_text_present("Quick Actions", timeout=4)

    def pull_to_refresh(self):
        try:
            self.driver.execute_script(
                "mobile: scrollGesture",
                {"direction": "down", "percent": 1.0},
            )
        except Exception:  # noqa: BLE001
            pass