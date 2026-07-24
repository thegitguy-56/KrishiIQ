"""
Test Data Framework — centralised test data for all test modules.
Provides valid, invalid, boundary, and security payloads.
"""
from dataclasses import dataclass, field
from typing import List


# ─────────────────────────────────────────────────────────────────────────────
# User Credential Sets
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class UserCredential:
    phone:    str
    password: str
    role:     str
    expected: str  # "success" | "unauthorized" | "failure"


USERS = {
    "officer": UserCredential("9000000001", "officer123",  "officer", "success"),
    "admin":   UserCredential("9000000003", "admin123",    "admin",   "success"),
    "farmer":  UserCredential("9000000002", "farmer123",   "farmer",  "unauthorized"),
}

INVALID_CREDENTIALS: List[UserCredential] = [
    UserCredential("0000000000", "wrongpass",    "none", "failure"),
    UserCredential("9000000001", "WrongPass123", "none", "failure"),
    UserCredential("",           "",             "none", "failure"),
    UserCredential("9000000001", "",             "none", "failure"),
    UserCredential("",           "officer123",   "none", "failure"),
    UserCredential("1234567890", "password",     "none", "failure"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Security Payloads
# ─────────────────────────────────────────────────────────────────────────────

SQL_INJECTIONS = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "' UNION SELECT 1,2,3 --",
    "1' AND '1'='1",
    "admin'--",
]

XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)",
    "<svg/onload=alert(1)>",
    "';alert(1)//",
]

PATH_TRAVERSAL = [
    "../etc/passwd",
    "../../windows/system32",
    "%2e%2e%2f",
]

BOUNDARY_PHONES = [
    ("", "empty"),
    ("1", "single_digit"),
    ("123", "too_short"),
    ("9" * 10, "exact_10"),
    ("9" * 15, "15_digits"),
    ("9" * 50, "very_long"),
    ("+91 9000000001", "with_country_code"),
    ("900-000-0001", "with_dashes"),
    ("900 000 0001", "with_spaces"),
    ("abc1234567", "alphanumeric"),
    ("!@#$%^&*()", "special_chars"),
]

BOUNDARY_PASSWORDS = [
    ("", "empty"),
    ("a", "single_char"),
    ("abc", "too_short"),
    ("x" * 100, "very_long"),
    ("   ", "whitespace_only"),
    (f" {'officer123'} ", "with_spaces"),
    ("Officer123", "wrong_case"),
    ("OFFICER123", "uppercase"),
    ("officer123 ", "trailing_space"),
]

SEARCH_INPUTS = [
    ("", "empty"),
    ("a", "single_char"),
    ("Coimbatore", "valid_district"),
    ("zzznomatch", "no_results"),
    ("!@#$%", "special_chars"),
    ("<script>", "xss_attempt"),
    ("a" * 200, "very_long"),
    ("தமிழ்", "unicode_tamil"),
    ("🌾", "emoji"),
    ("   ", "spaces_only"),
]


# ─────────────────────────────────────────────────────────────────────────────
# App Routes
# ─────────────────────────────────────────────────────────────────────────────

PROTECTED_ROUTES = [
    "/dashboard",
    "/farmers",
    "/map",
    "/disease-alerts",
    "/analytics",
]

PUBLIC_ROUTES = [
    "/login",
    "/unauthorized",
]

SEVERITY_OPTIONS = [
    ("high",   "High & Critical only"),
    ("medium", "Medium & above"),
]

VIEWPORTS = [
    (375,  812,  "mobile"),
    (768,  1024, "tablet"),
    (1024, 768,  "small_desktop"),
    (1366, 768,  "hd_desktop"),
    (1920, 1080, "full_hd"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Expected UI Text
# ─────────────────────────────────────────────────────────────────────────────

EXPECTED_TEXT = {
    "login_logo":          "KrishiIQ",
    "login_portal_label":  "Officer & Admin Portal",
    "login_farmer_notice": "Farmers: use the mobile app",
    "login_submit_btn":    "Sign In",
    "login_demo_hint":     "Demo:",
    "dashboard_heading":   "District Overview",
    "farmers_heading":     "Farmers",
    "disease_heading":     "Disease Alerts",
    "yield_chart":         "Crop Yield Trends",
    "farm_count_chart":    "Farm Count by District",
    "recent_alerts":       "Recent Disease Alerts",
}

TABLE_COLUMNS = {
    "farmers": ["Farmer", "District", "Farms", "Area (ac)", "Crops", "Status"],
    "dashboard_alerts": ["Disease", "Severity", "Date"],
}

STATUS_BADGES = ["ALERT", "HEALTHY"]
SEVERITY_BADGES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
