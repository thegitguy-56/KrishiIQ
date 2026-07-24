"""
BasePage — shared helpers for all Page Objects.
"""
import logging
import os
import time
from datetime import datetime
from typing import Optional, List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    StaleElementReferenceException, ElementClickInterceptedException,
)

import config

logger = logging.getLogger(__name__)


class BasePage:
    """All Page Objects inherit from this class."""

    def __init__(self, driver: WebDriver):
        self.driver  = driver
        self.wait    = WebDriverWait(driver, config.EXPLICIT_WAIT, poll_frequency=0.5,
                                     ignored_exceptions=[StaleElementReferenceException])
        self.actions = ActionChains(driver)

    # ── Navigation ──────────────────────────────────────────────────────────────

    def open(self, path: str = "") -> None:
        url = config.BASE_URL.rstrip("/") + path
        logger.info("Navigating to %s", url)
        self.driver.get(url)

    def get_current_url(self) -> str:
        return self.driver.current_url

    def get_title(self) -> str:
        return self.driver.title

    def refresh(self) -> None:
        self.driver.refresh()

    def go_back(self) -> None:
        self.driver.back()

    def go_forward(self) -> None:
        self.driver.forward()

    # ── Element Finders (explicit waits) ────────────────────────────────────────

    def find(self, by: str, value: str, timeout: int = None) -> WebElement:
        t = timeout or config.EXPLICIT_WAIT
        try:
            return WebDriverWait(self.driver, t).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            self._screenshot(f"find_timeout_{value[:20]}")
            raise

    def find_visible(self, by: str, value: str, timeout: int = None) -> WebElement:
        t = timeout or config.EXPLICIT_WAIT
        try:
            return WebDriverWait(self.driver, t).until(
                EC.visibility_of_element_located((by, value))
            )
        except TimeoutException:
            self._screenshot(f"visible_timeout_{value[:20]}")
            raise

    def find_clickable(self, by: str, value: str, timeout: int = None) -> WebElement:
        t = timeout or config.EXPLICIT_WAIT
        try:
            return WebDriverWait(self.driver, t).until(
                EC.element_to_be_clickable((by, value))
            )
        except TimeoutException:
            self._screenshot(f"clickable_timeout_{value[:20]}")
            raise

    def find_all(self, by: str, value: str, timeout: int = None) -> List[WebElement]:
        t = timeout or config.EXPLICIT_WAIT
        try:
            WebDriverWait(self.driver, t).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            pass
        return self.driver.find_elements(by, value)

    def is_present(self, by: str, value: str, timeout: int = 3) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except TimeoutException:
            return False

    def is_visible(self, by: str, value: str, timeout: int = 3) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return True
        except TimeoutException:
            return False

    def wait_for_url_contains(self, fragment: str, timeout: int = None) -> bool:
        t = timeout or config.EXPLICIT_WAIT
        try:
            return WebDriverWait(self.driver, t).until(
                EC.url_contains(fragment)
            )
        except TimeoutException:
            return False

    def wait_for_text_in_element(self, by: str, value: str, text: str, timeout: int = None) -> bool:
        t = timeout or config.EXPLICIT_WAIT
        try:
            return WebDriverWait(self.driver, t).until(
                EC.text_to_be_present_in_element((by, value), text)
            )
        except TimeoutException:
            return False

    def wait_invisible(self, by: str, value: str, timeout: int = None) -> bool:
        t = timeout or config.EXPLICIT_WAIT
        try:
            return WebDriverWait(self.driver, t).until(
                EC.invisibility_of_element_located((by, value))
            )
        except TimeoutException:
            return False

    # ── Interactions ────────────────────────────────────────────────────────────

    def click(self, by: str, value: str) -> None:
        el = self.find_clickable(by, value)
        try:
            el.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", el)

    def type_text(self, by: str, value: str, text: str, clear: bool = True) -> None:
        el = self.find_visible(by, value)
        if clear:
            el.clear()
        el.send_keys(text)

    def get_text(self, by: str, value: str) -> str:
        return self.find_visible(by, value).text.strip()

    def get_attribute(self, by: str, value: str, attr: str) -> str:
        return self.find(by, value).get_attribute(attr) or ""

    def select_by_visible_text(self, by: str, value: str, text: str) -> None:
        el = self.find(by, value)
        Select(el).select_by_visible_text(text)

    def select_by_value(self, by: str, value: str, option_value: str) -> None:
        el = self.find(by, value)
        Select(el).select_by_value(option_value)

    def get_selected_option(self, by: str, value: str) -> str:
        el = self.find(by, value)
        return Select(el).first_selected_option.text.strip()

    def scroll_to(self, by: str, value: str) -> None:
        el = self.find(by, value)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)

    def scroll_to_bottom(self) -> None:
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def hover(self, by: str, value: str) -> None:
        el = self.find_visible(by, value)
        self.actions.move_to_element(el).perform()

    def press_key(self, by: str, value: str, key) -> None:
        self.find_visible(by, value).send_keys(key)

    def execute_js(self, script: str, *args):
        return self.driver.execute_script(script, *args)

    # ── Screenshots ─────────────────────────────────────────────────────────────

    def _screenshot(self, name: str = "screenshot") -> Optional[str]:
        import re
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', name)
        os.makedirs(config.SCREENSHOTS_DIR, exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = os.path.join(config.SCREENSHOTS_DIR, f"{safe_name}_{ts}.png")
        try:
            self.driver.save_screenshot(path)
            logger.info("Screenshot saved: %s", path)
            return path
        except Exception as exc:
            logger.warning("Screenshot failed: %s", exc)
            return None

    def take_screenshot(self, name: str = "screenshot") -> Optional[str]:
        return self._screenshot(name)

    # ── Assertions Helpers ───────────────────────────────────────────────────────

    def assert_url_contains(self, fragment: str) -> None:
        current = self.get_current_url()
        assert fragment in current, f"Expected URL to contain '{fragment}', got: {current}"

    def assert_text_equals(self, by: str, value: str, expected: str) -> None:
        actual = self.get_text(by, value)
        assert actual == expected, f"Expected text '{expected}', got '{actual}'"

    def assert_text_contains(self, by: str, value: str, expected: str) -> None:
        actual = self.get_text(by, value)
        assert expected in actual, f"Expected '{expected}' in text '{actual}'"

    def assert_element_visible(self, by: str, value: str) -> None:
        assert self.is_visible(by, value), f"Element not visible: {by}={value}"

    def assert_element_present(self, by: str, value: str) -> None:
        assert self.is_present(by, value), f"Element not present: {by}={value}"

    # ── Utility ──────────────────────────────────────────────────────────────────

    def get_page_source(self) -> str:
        return self.driver.page_source

    def get_all_links(self) -> List[str]:
        return [a.get_attribute("href") for a in
                self.driver.find_elements(By.TAG_NAME, "a") if a.get_attribute("href")]

    def count_elements(self, by: str, value: str) -> int:
        return len(self.driver.find_elements(by, value))

    def set_viewport(self, width: int, height: int) -> None:
        self.driver.set_window_size(width, height)

    def get_element_color(self, by: str, value: str, prop: str = "color") -> str:
        el = self.find(by, value)
        return self.driver.execute_script(
            f"return window.getComputedStyle(arguments[0]).{prop};", el
        )

    def is_element_enabled(self, by: str, value: str) -> bool:
        return self.find(by, value).is_enabled()

    def is_element_selected(self, by: str, value: str) -> bool:
        return self.find(by, value).is_selected()

    def clear_field(self, by: str, value: str) -> None:
        el = self.find(by, value)
        el.clear()
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
