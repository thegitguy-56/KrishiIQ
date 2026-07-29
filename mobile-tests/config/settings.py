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

    # Applied as the Python-process-wide default socket timeout (see
    # conftest.py). Bounds every Appium HTTP call, including the
    # FlutterDriver/Observatory ones that have been observed to hang
    # indefinitely with no error and no timeout of their own.
    #
    # Was 45s, based on an EXPLICIT_WAIT=20s "slowest legitimate wait"
    # that turned out to be dead config — nothing in this suite actually
    # blocks on it. Measured from a real CI run instead: appium-server.log
    # from one timed-out shard (2h wall clock, killed by the job timeout)
    # showed 113 of these calls hanging the full 45s before failing —
    # ~85 of the shard's 114 total minutes, i.e. most of the run was pure
    # dead waiting on calls that were always going to fail, not doing
    # test work. Every *legitimate* call observed in healthy logs
    # completes in well under a second, with the slowest being ~3.9s
    # (activate_app's Observatory reconnect). 12s keeps ~3x headroom over
    # that while cutting the wasted-call cost ~4x (45s -> 12s), so the
    # same 113 stuck calls cost ~23 minutes instead of ~85.
    APPIUM_COMMAND_TIMEOUT = int(os.getenv("APPIUM_COMMAND_TIMEOUT", "12"))

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