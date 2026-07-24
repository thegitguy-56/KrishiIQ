"""
DashboardPage — Page Object for /dashboard
"""
from selenium.webdriver.common.by import By
from .base_page import BasePage
import config


class DashboardPage(BasePage):
    # ── Locators ──────────────────────────────────────────────────────────────
    PAGE_HEADING      = (By.XPATH, "//h1[contains(text(),'District Overview')]")
    STAT_CARDS        = (By.CSS_SELECTOR, ".card, [class*='stat']")
    CHART_CONTAINER   = (By.CSS_SELECTOR, ".recharts-wrapper, [class*='recharts']")
    BAR_CHART         = (By.CSS_SELECTOR, ".recharts-bar, [class*='bar-chart']")
    LINE_CHART        = (By.CSS_SELECTOR, ".recharts-line, [class*='line-chart']")
    ALERTS_TABLE      = (By.XPATH, "//h2[contains(text(),'Recent Disease Alerts')]")
    LOADING_INDICATOR = (By.XPATH, "//*[contains(text(),'Loading dashboard')]")
    NAV_DASHBOARD     = (By.XPATH, "//a[contains(@href,'dashboard') or contains(text(),'Dashboard')]")
    NAV_FARMERS       = (By.XPATH, "//a[contains(@href,'farmers') or contains(text(),'Farmers')]")
    NAV_MAP           = (By.XPATH, "//a[contains(@href,'map') or contains(text(),'Map')]")
    NAV_DISEASE       = (By.XPATH, "//a[contains(@href,'disease') or contains(text(),'Disease')]")
    NAV_ANALYTICS     = (By.XPATH, "//a[contains(@href,'analytics') or contains(text(),'Analytics')]")
    SIDEBAR           = (By.CSS_SELECTOR, "nav, aside, [class*='sidebar'], [class*='nav']")
    TOTAL_FARMERS     = (By.XPATH, "//*[contains(text(),'Total Farmers')]")
    TOTAL_FARMS       = (By.XPATH, "//*[contains(text(),'Total Farms')]")
    DISEASE_ALERTS_STAT = (By.XPATH, "//*[contains(text(),'Active Disease Alerts')]")
    AREA_STAT         = (By.XPATH, "//*[contains(text(),'Area')]")
    YIELD_CHART_HEADING = (By.XPATH, "//h2[contains(text(),'Yield Trends')]")
    FARM_COUNT_HEADING  = (By.XPATH, "//h2[contains(text(),'Farm Count')]")

    # ── Actions ───────────────────────────────────────────────────────────────

    def load(self) -> "DashboardPage":
        self.open(config.ROUTES["dashboard"])
        self.wait_for_url_contains("dashboard")
        return self

    def wait_for_page_load(self) -> "DashboardPage":
        self.wait_invisible(*self.LOADING_INDICATOR, timeout=30)
        return self

    def navigate_to_farmers(self) -> None:
        self.click(*self.NAV_FARMERS)

    def navigate_to_map(self) -> None:
        self.click(*self.NAV_MAP)

    def navigate_to_disease_alerts(self) -> None:
        self.click(*self.NAV_DISEASE)

    def navigate_to_analytics(self) -> None:
        self.click(*self.NAV_ANALYTICS)

    # ── Queries ───────────────────────────────────────────────────────────────

    def is_heading_visible(self) -> bool:
        return self.is_visible(*self.PAGE_HEADING)

    def is_sidebar_visible(self) -> bool:
        return self.is_present(*self.SIDEBAR)

    def has_charts(self) -> bool:
        return self.count_elements(*self.CHART_CONTAINER) > 0

    def has_stat_cards(self) -> bool:
        return self.count_elements(*self.STAT_CARDS) > 0

    def is_total_farmers_visible(self) -> bool:
        return self.is_visible(*self.TOTAL_FARMERS)

    def is_total_farms_visible(self) -> bool:
        return self.is_visible(*self.TOTAL_FARMS)

    def is_alerts_stat_visible(self) -> bool:
        return self.is_visible(*self.DISEASE_ALERTS_STAT)

    def get_stat_card_count(self) -> int:
        return self.count_elements(*self.STAT_CARDS)

    def is_on_dashboard(self) -> bool:
        return "dashboard" in self.get_current_url()

    def get_page_heading_text(self) -> str:
        return self.get_text(*self.PAGE_HEADING)
