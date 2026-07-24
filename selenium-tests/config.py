"""
KrishiIQ Selenium Test Framework - Configuration
"""
import os

# ─── Base URL ─────────────────────────────────────────────────────────────────
BASE_URL = os.environ.get("BASE_URL", "https://thegitguy-56.github.io/KrishiIQ/")

# ─── Browser ──────────────────────────────────────────────────────────────────
BROWSER = os.environ.get("BROWSER", "chrome")
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
WINDOW_WIDTH = int(os.environ.get("WINDOW_WIDTH", "1920"))
WINDOW_HEIGHT = int(os.environ.get("WINDOW_HEIGHT", "1080"))

# ─── Timeouts (seconds) ───────────────────────────────────────────────────────
IMPLICIT_WAIT = 0          # Always use explicit waits
EXPLICIT_WAIT = 20         # Default explicit wait
PAGE_LOAD_TIMEOUT = 60     # Max page load time
RETRY_ATTEMPTS = 2         # Flaky-test reruns

# ─── Test Credentials ─────────────────────────────────────────────────────────
OFFICER_PHONE    = os.environ.get("OFFICER_PHONE",    "9000000001")
OFFICER_PASSWORD = os.environ.get("OFFICER_PASSWORD", "officer123")
ADMIN_PHONE      = os.environ.get("ADMIN_PHONE",      "9000000003")
ADMIN_PASSWORD   = os.environ.get("ADMIN_PASSWORD",   "admin123")
FARMER_PHONE     = os.environ.get("FARMER_PHONE",     "9000000002")
FARMER_PASSWORD  = os.environ.get("FARMER_PASSWORD",  "farmer123")

# ─── Invalid Credentials ──────────────────────────────────────────────────────
INVALID_PHONE    = "0000000000"
INVALID_PASSWORD = "wrongpassword"
EMPTY_STRING     = ""
SHORT_PHONE      = "123"
LONG_PHONE       = "9" * 20
SQL_INJECTION    = "' OR '1'='1"
XSS_PAYLOAD      = "<script>alert('xss')</script>"

# ─── Paths ────────────────────────────────────────────────────────────────────
REPORTS_DIR     = os.path.join(os.path.dirname(__file__), "reports")
SCREENSHOTS_DIR = os.path.join(REPORTS_DIR, "screenshots")
LOGS_DIR        = os.path.join(REPORTS_DIR, "logs")
EXCEL_REPORT    = os.path.join(REPORTS_DIR, "Automation_Test_Report.xlsx")
HTML_REPORT     = os.path.join(REPORTS_DIR, "execution-report.html")
DASHBOARD_HTML  = os.path.join(REPORTS_DIR, "dashboard.html")
JSON_REPORT     = os.path.join(REPORTS_DIR, "execution-results.json")
SUMMARY_MD      = os.path.join(REPORTS_DIR, "summary.md")

# ─── App Routes ───────────────────────────────────────────────────────────────
ROUTES = {
    "login":          "/login",
    "dashboard":      "/dashboard",
    "farmers":        "/farmers",
    "map":            "/map",
    "disease_alerts": "/disease-alerts",
    "analytics":      "/analytics",
    "unauthorized":   "/unauthorized",
}

# ─── Viewport Breakpoints ─────────────────────────────────────────────────────
VIEWPORTS = {
    "mobile":  (375,  812),
    "tablet":  (768,  1024),
    "desktop": (1920, 1080),
    "hd":      (1366, 768),
}
