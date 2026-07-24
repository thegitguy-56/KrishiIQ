"""
Driver factory — creates headless Chrome/Firefox WebDriver instances.
"""
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService

try:
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
    USE_WDM = True
except ImportError:
    USE_WDM = False

import config

logger = logging.getLogger(__name__)


def create_driver(browser: str = None, headless: bool = None) -> webdriver.Remote:
    """Return a configured WebDriver instance."""
    browser   = (browser  or config.BROWSER).lower()
    headless  = headless if headless is not None else config.HEADLESS

    if browser == "firefox":
        return _create_firefox(headless)
    return _create_chrome(headless)


def _create_chrome(headless: bool) -> webdriver.Chrome:
    opts = ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-infobars")
    opts.add_argument(f"--window-size={config.WINDOW_WIDTH},{config.WINDOW_HEIGHT}")
    opts.add_argument("--lang=en-US")
    opts.add_argument("--remote-debugging-port=0")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    opts.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
    })

    # browser-actions/setup-chrome sets CHROME_PATH in CI
    chrome_binary = os.environ.get("CHROME_PATH", "")

    if chrome_binary:
        opts.binary_location = chrome_binary
        logger.info("Using Chrome binary from env: %s", chrome_binary)

    # Let Selenium 4 (Selenium Manager) handle ChromeDriver automatically
    svc = ChromeService()

    driver = webdriver.Chrome(service=svc, options=opts)
    driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
    driver.implicitly_wait(config.IMPLICIT_WAIT)
    driver.set_window_size(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    logger.info("Chrome driver created (headless=%s)", headless)
    return driver


def _create_firefox(headless: bool) -> webdriver.Firefox:
    opts = FirefoxOptions()
    if headless:
        opts.add_argument("--headless")
    opts.set_preference("intl.accept_languages", "en-US")

    if USE_WDM:
        svc = FirefoxService(GeckoDriverManager().install())
    else:
        svc = FirefoxService()

    driver = webdriver.Firefox(service=svc, options=opts)
    driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
    driver.implicitly_wait(config.IMPLICIT_WAIT)
    driver.set_window_size(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    logger.info("Firefox driver created (headless=%s)", headless)
    return driver
