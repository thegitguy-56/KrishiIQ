"""
DiseaseAlertsPage — Page Object for /disease-alerts
"""
from selenium.webdriver.common.by import By
from .base_page import BasePage
import config


class DiseaseAlertsPage(BasePage):
    # ── Locators ──────────────────────────────────────────────────────────────
    PAGE_HEADING      = (By.XPATH, "//h1[contains(text(),'Disease Alerts')]")
    DISTRICT_SELECT   = (By.XPATH, "(//select)[1]")
    SEVERITY_SELECT   = (By.XPATH, "(//select)[2]")
    REFRESH_BTN       = (By.XPATH, "//button[contains(text(),'Refresh')]")
    ALERT_CARDS       = (By.CSS_SELECTOR, ".card")
    LOADING_TEXT      = (By.XPATH, "//*[contains(text(),'Loading alerts')]")
    NO_ALERTS_MSG     = (By.XPATH, "//*[contains(text(),'No') and contains(text(),'severity alerts')]")
    CRITICAL_BADGE    = (By.XPATH, "//span[contains(text(),'CRITICAL')]")
    HIGH_BADGE        = (By.XPATH, "//span[contains(text(),'HIGH')]")
    PEST_BADGE        = (By.XPATH, "//span[contains(text(),'PEST ANOMALY')]")
    CONFIDENCE_TEXT   = (By.XPATH, "//*[contains(text(),'Confidence:')]")
    AFFECTED_TEXT     = (By.XPATH, "//*[contains(text(),'Affected:')]")
    SPINNING_ICON     = (By.CSS_SELECTOR, "[class*='animate-spin']")

    # ── Actions ───────────────────────────────────────────────────────────────

    def load(self) -> "DiseaseAlertsPage":
        self.open(config.ROUTES["disease_alerts"])
        self.wait_for_url_contains("disease-alerts")
        return self

    def wait_for_load(self) -> "DiseaseAlertsPage":
        self.wait_invisible(*self.LOADING_TEXT, timeout=30)
        return self

    def select_district(self, district: str) -> "DiseaseAlertsPage":
        self.select_by_visible_text(*self.DISTRICT_SELECT, district)
        return self

    def select_severity(self, severity_label: str) -> "DiseaseAlertsPage":
        self.select_by_visible_text(*self.SEVERITY_SELECT, severity_label)
        return self

    def click_refresh(self) -> "DiseaseAlertsPage":
        self.click(*self.REFRESH_BTN)
        return self

    def get_selected_district(self) -> str:
        return self.get_selected_option(*self.DISTRICT_SELECT)

    def get_selected_severity(self) -> str:
        return self.get_selected_option(*self.SEVERITY_SELECT)

    # ── Queries ───────────────────────────────────────────────────────────────

    def is_heading_visible(self) -> bool:
        return self.is_visible(*self.PAGE_HEADING)

    def is_district_filter_visible(self) -> bool:
        return self.is_visible(*self.DISTRICT_SELECT)

    def is_severity_filter_visible(self) -> bool:
        return self.is_visible(*self.SEVERITY_SELECT)

    def is_refresh_button_visible(self) -> bool:
        return self.is_visible(*self.REFRESH_BTN)

    def get_alert_card_count(self) -> int:
        return self.count_elements(*self.ALERT_CARDS)

    def has_no_alerts_message(self) -> bool:
        return self.is_visible(*self.NO_ALERTS_MSG)

    def has_critical_alerts(self) -> bool:
        return self.is_present(*self.CRITICAL_BADGE, timeout=5)

    def has_high_alerts(self) -> bool:
        return self.is_present(*self.HIGH_BADGE, timeout=5)

    def has_confidence_score(self) -> bool:
        return self.is_present(*self.CONFIDENCE_TEXT, timeout=5)

    def is_on_disease_alerts_page(self) -> bool:
        return "disease-alerts" in self.get_current_url()
