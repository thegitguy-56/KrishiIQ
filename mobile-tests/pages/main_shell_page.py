from pages.base_page import BasePage


class MainShellPage(BasePage):
    """Bottom NavigationBar destinations. These use FlutterFinder's
    by_text() because the app's NavigationDestination labels are already
    unique, so no extra ValueKeys were required in main_shell.dart."""

    TABS = ["Home", "Advisory", "Sensors", "History", "Profile"]

    def go_to_tab(self, label: str):
        assert label in self.TABS, f"Unknown tab '{label}', expected one of {self.TABS}"
        self.tap(self.by_text(label))
        self.wait(1)

    def go_home(self):
        self.go_to_tab("Home")

    def go_advisory(self):
        self.go_to_tab("Advisory")

    def go_sensors(self):
        self.go_to_tab("Sensors")

    def go_history(self):
        self.go_to_tab("History")

    def go_profile(self):
        self.go_to_tab("Profile")
