"""
AnalyticsPage — Page Object for /analytics
MapPage — Page Object for /map
"""
from selenium.webdriver.common.by import By
from .base_page import BasePage
import config


class AnalyticsPage(BasePage):
    PAGE_HEADING    = (By.XPATH, "//h1[contains(text(),'Analytics') or contains(text(),'analytics')]")
    CHART_CONTAINER = (By.CSS_SELECTOR, ".recharts-wrapper")
    LOADING_TEXT    = (By.XPATH, "//*[contains(text(),'Loading')]")
    CARD            = (By.CSS_SELECTOR, ".card")

    def load(self) -> "AnalyticsPage":
        self.open(config.ROUTES["analytics"])
        self.wait_for_url_contains("analytics")
        return self

    def is_heading_visible(self) -> bool:
        return self.is_present(*self.PAGE_HEADING, timeout=10)

    def has_charts(self) -> bool:
        return self.count_elements(*self.CHART_CONTAINER) > 0

    def is_on_analytics_page(self) -> bool:
        return "analytics" in self.get_current_url()

    def get_card_count(self) -> int:
        return self.count_elements(*self.CARD)


class MapPage(BasePage):
    PAGE_HEADING    = (By.XPATH, "//h1[contains(text(),'Map') or contains(text(),'Farm')]")
    MAP_CONTAINER   = (By.CSS_SELECTOR, ".leaflet-container, [class*='map']")
    LOADING_TEXT    = (By.XPATH, "//*[contains(text(),'Loading')]")

    def load(self) -> "MapPage":
        self.open(config.ROUTES["map"])
        self.wait_for_url_contains("map")
        return self

    def is_map_visible(self) -> bool:
        return self.is_present(*self.MAP_CONTAINER, timeout=15)

    def is_on_map_page(self) -> bool:
        return "map" in self.get_current_url()


class UnauthorizedPage(BasePage):
    HEADING = (By.XPATH, "//h1 | //*[contains(text(),'Unauthorized') or contains(text(),'unauthorized') or contains(text(),'403')]")

    def load(self) -> "UnauthorizedPage":
        self.open(config.ROUTES["unauthorized"])
        return self

    def is_on_unauthorized_page(self) -> bool:
        return "unauthorized" in self.get_current_url()

    def is_heading_visible(self) -> bool:
        return self.is_present(*self.HEADING, timeout=5)
