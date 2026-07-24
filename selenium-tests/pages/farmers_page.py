"""
FarmersPage — Page Object for /farmers
"""
from selenium.webdriver.common.by import By
from .base_page import BasePage
import config


class FarmersPage(BasePage):
    # ── Locators ──────────────────────────────────────────────────────────────
    PAGE_HEADING      = (By.XPATH, "//h1[contains(text(),'Farmers')]")
    FARMER_COUNT_SPAN = (By.XPATH, "//span[contains(text(),'registered')]")
    SEARCH_INPUT      = (By.CSS_SELECTOR, "input[placeholder*='Search']")
    TABLE             = (By.CSS_SELECTOR, "table")
    TABLE_ROWS        = (By.CSS_SELECTOR, "tbody tr")
    TH_FARMER         = (By.XPATH, "//th[contains(text(),'Farmer')]")
    TH_DISTRICT       = (By.XPATH, "//th[contains(text(),'District')]")
    TH_FARMS          = (By.XPATH, "//th[contains(text(),'Farms')]")
    TH_AREA           = (By.XPATH, "//th[contains(text(),'Area')]")
    TH_CROPS          = (By.XPATH, "//th[contains(text(),'Crops')]")
    TH_STATUS         = (By.XPATH, "//th[contains(text(),'Status')]")
    LOADING_TEXT      = (By.XPATH, "//*[contains(text(),'Loading farmers')]")
    STATUS_ALERT      = (By.XPATH, "//span[contains(@class,'badge') and contains(text(),'ALERT')]")
    STATUS_HEALTHY    = (By.XPATH, "//span[contains(@class,'badge') and contains(text(),'HEALTHY')]")
    EMPTY_STATE       = (By.CSS_SELECTOR, "tbody:empty, [class*='empty']")

    # ── Actions ───────────────────────────────────────────────────────────────

    def load(self) -> "FarmersPage":
        self.open(config.ROUTES["farmers"])
        self.wait_for_url_contains("farmers")
        return self

    def wait_for_table(self) -> "FarmersPage":
        """Wait for the farmers table to load. Resilient to API being down."""
        import time
        # First wait for loading text to disappear (short timeout)
        self.wait_invisible(*self.LOADING_TEXT, timeout=10)
        # Also try to wait for the table itself
        try:
            self.find(*self.TABLE, timeout=5)
        except Exception:
            pass  # Table may not appear if API is down
        time.sleep(0.5)  # Small settle time for React re-renders
        return self

    def search(self, query: str) -> "FarmersPage":
        self.type_text(*self.SEARCH_INPUT, query)
        return self

    def clear_search(self) -> "FarmersPage":
        self.clear_field(*self.SEARCH_INPUT)
        return self

    # ── Queries ───────────────────────────────────────────────────────────────

    def is_heading_visible(self) -> bool:
        return self.is_visible(*self.PAGE_HEADING)

    def is_table_visible(self) -> bool:
        return self.is_visible(*self.TABLE)

    def get_row_count(self) -> int:
        return self.count_elements(*self.TABLE_ROWS)

    def get_farmer_count_text(self) -> str:
        return self.get_text(*self.FARMER_COUNT_SPAN)

    def is_search_input_visible(self) -> bool:
        return self.is_visible(*self.SEARCH_INPUT)

    def has_farmer_column(self) -> bool:
        return self.is_visible(*self.TH_FARMER)

    def has_district_column(self) -> bool:
        return self.is_visible(*self.TH_DISTRICT)

    def has_status_column(self) -> bool:
        return self.is_visible(*self.TH_STATUS)

    def get_first_farmer_name(self) -> str:
        rows = self.find_all(*self.TABLE_ROWS)
        if rows:
            return rows[0].find_elements(By.TAG_NAME, "td")[0].text.strip()
        return ""

    def has_alert_badges(self) -> bool:
        return self.is_present(*self.STATUS_ALERT, timeout=5)

    def has_healthy_badges(self) -> bool:
        return self.is_present(*self.STATUS_HEALTHY, timeout=5)

    def get_alert_count(self) -> int:
        return self.count_elements(*self.STATUS_ALERT)

    def is_search_placeholder_correct(self) -> bool:
        placeholder = self.get_attribute(*self.SEARCH_INPUT, "placeholder")
        return "Search" in placeholder or "search" in placeholder

    def is_on_farmers_page(self) -> bool:
        return "farmers" in self.get_current_url()
