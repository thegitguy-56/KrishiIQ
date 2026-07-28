from pages.base_page import BasePage


class MainShellPage(BasePage):
    """Bottom NavigationBar destinations.

    These use by_key(), not by_text(). Material 3's NavigationBar renders
    each destination label as TWO simultaneous Text widgets (one for the
    selected state, one for the unselected state) so it can crossfade
    between them — both are hit-testable at once regardless of which tab
    is currently active. That made by_text('Advisory') etc. ambiguous and
    every tap raised "ambiguously found multiple matching widgets". Each
    NavigationDestination in main_shell.dart now carries its own
    ValueKey (nav_home, nav_advisory, nav_sensors, nav_history,
    nav_profile) which resolves to exactly one widget.
    """

    TABS = ["Home", "Advisory", "Sensors", "History", "Profile"]

    def go_to_tab(self, label: str):
        assert label in self.TABS, f"Unknown tab '{label}', expected one of {self.TABS}"
        self.tap(self.by_key(f"nav_{label.lower()}"))
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