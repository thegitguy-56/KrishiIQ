"""
Central, environment-driven configuration for the mobile test suite.
Every value can be overridden by a GitHub Actions env var, so nothing here
needs to be hardcoded for CI vs local debugging.
"""
import os


class Settings:
    APPIUM_HOST = os.getenv("APPIUM_HOST", "127.0.0.1")
    APPIUM_PORT = os.getenv("APPIUM_PORT", "4723")
    APPIUM_BASE_PATH = os.getenv("APPIUM_BASE_PATH", "/wd/hub")
    APPIUM_SERVER_URL = f"http://{APPIUM_HOST}:{APPIUM_PORT}{APPIUM_BASE_PATH}"

    PLATFORM_NAME = os.getenv("PLATFORM_NAME", "Android")
    PLATFORM_VERSION = os.getenv("PLATFORM_VERSION", "13")
    DEVICE_NAME = os.getenv("DEVICE_NAME", "emulator-5554")
    AUTOMATION_NAME = os.getenv("AUTOMATION_NAME", "Flutter")

    APK_PATH = os.getenv(
        "APK_PATH",
        "mobile/build/app/outputs/flutter-apk/app-debug.apk",
    )
    APP_PACKAGE = os.getenv("APP_PACKAGE", "com.krishiiq.krishiiq")
    APP_ACTIVITY = os.getenv("APP_ACTIVITY", ".MainActivity")

    IMPLICIT_WAIT = int(os.getenv("IMPLICIT_WAIT", "10"))
    EXPLICIT_WAIT = int(os.getenv("EXPLICIT_WAIT", "20"))
    NEW_COMMAND_TIMEOUT = int(os.getenv("NEW_COMMAND_TIMEOUT", "120"))

    # Seeded/test backend credentials (mirrors selenium-tests.yml conventions)
    FARMER_PHONE = os.getenv("FARMER_PHONE", "9000000002")
    FARMER_PASSWORD = os.getenv("FARMER_PASSWORD", "farmer123")
    OFFICER_PHONE = os.getenv("OFFICER_PHONE", "9000000001")
    OFFICER_PASSWORD = os.getenv("OFFICER_PASSWORD", "officer123")
    ADMIN_PHONE = os.getenv("ADMIN_PHONE", "9000000003")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

    BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "https://krishiiq-6su1.onrender.com")

    # NOTE: relative to pytest's cwd, which ci_run_shard.sh already `cd`s into
    # mobile-tests/ before running pytest. A "mobile-tests/reports" default
    # here double-nests to mobile-tests/mobile-tests/reports/... and silently
    # misses the screenshots/logs paths the workflow uploads from.
    REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")
    SCREENSHOTS_DIR = os.path.join(REPORTS_DIR, "screenshots")
    LOGS_DIR = os.path.join(REPORTS_DIR, "logs")

    RERUN_COUNT = int(os.getenv("RERUN_COUNT", "2"))
    RERUN_DELAY = int(os.getenv("RERUN_DELAY", "2"))
    PARALLEL_WORKERS = os.getenv("PARALLEL_WORKERS", "auto")


settings = Settings()
