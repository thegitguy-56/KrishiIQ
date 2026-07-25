"""
Data factory: every list here feeds pytest.mark.parametrize calls across
the test modules. Keeping the data centralized means the same invalid-phone
set (for example) is reused consistently across Authentication, Forms and
Input Validation modules instead of being redefined per file.
"""

VALID_FARMER = {
    "phone": "9000000002",
    "password": "farmer123",
}
VALID_OFFICER = {
    "phone": "9000000001",
    "password": "officer123",
}
VALID_ADMIN = {
    "phone": "9000000003",
    "password": "admin123",
}

# -- invalid / boundary phone numbers --------------------------------------
INVALID_PHONES = [
    ("", "empty"),
    ("123", "too_short"),
    ("12345678901234", "too_long"),
    ("abcdefghij", "alphabetic"),
    ("90000000-2", "special_char"),
    ("          ", "whitespace_only"),
    ("9000000002 ", "trailing_space"),
    (" 9000000002", "leading_space"),
    ("+919000000002999999", "malformed_country_code"),
    ("০৯০০০০০০০০২", "non_latin_digits"),
]

# -- invalid / boundary passwords ------------------------------------------
INVALID_PASSWORDS = [
    ("", "empty"),
    ("a", "single_char"),
    ("12345", "five_chars_below_min"),
    (" " * 8, "whitespace_only"),
    ("p@ss", "short_special"),
    ("A" * 129, "excessively_long"),
    ("wrongpass123", "wrong_but_valid_format"),
]

# -- injection / security payloads ------------------------------------------
INJECTION_PAYLOADS = [
    ("' OR '1'='1", "sql_injection_or"),
    ("'; DROP TABLE users; --", "sql_injection_drop"),
    ("<script>alert(1)</script>", "xss_script_tag"),
    ("{{7*7}}", "template_injection"),
    ("../../etc/passwd", "path_traversal"),
    ("%00", "null_byte"),
]

# -- invalid emails -----------------------------------------------------
INVALID_EMAILS = [
    ("", "empty"),
    ("plainaddress", "no_at_symbol"),
    ("@missinglocal.com", "missing_local_part"),
    ("missingdomain@", "missing_domain"),
    ("has space@example.com", "contains_space"),
    ("double@@example.com", "double_at"),
    ("trailing.dot.@example.com", "trailing_dot"),
]

# -- boundary farm data ------------------------------------------------
BOUNDARY_NUMBERS = [
    ("0", "zero"),
    ("-1", "negative"),
    ("0.0001", "tiny_decimal"),
    ("999999999", "very_large"),
    ("abc", "non_numeric"),
    ("1e10", "scientific_notation"),
    ("", "empty"),
]

LOCALES = ["en", "hi", "ta"]

CHAT_QUERIES = [
    ("What crop suits red soil?", "agronomy_question"),
    ("weather tomorrow", "weather_question"),
    ("", "empty_message"),
    ("a" * 500, "very_long_message"),
    ("🌾🌱🚜", "emoji_only"),
    ("SELECT * FROM users;", "sql_like_message"),
]

FARM_NAMES = [
    ("North Field", "normal"),
    ("A", "single_char"),
    ("A" * 100, "very_long"),
    ("Field #1 (2024)", "special_chars"),
    ("   ", "whitespace_only"),
]

SENSOR_DEVICE_IDS = [
    ("SENSOR-001", "normal"),
    ("", "empty"),
    ("S", "single_char"),
    ("SENSOR-" + "9" * 40, "very_long"),
    ("<img src=x onerror=alert(1)>", "xss_payload"),
]

NAV_ROUTES = [
    "/welcome",
    "/register",
    "/login",
    "/farm-setup",
    "/main",
    "/crop-health",
    "/irrigation",
    "/ai-chat",
    "/farm-map",
    "/farm-data",
    "/advisory",
    "/soildata",
]

BOTTOM_NAV_TABS = ["Home", "Advisory", "Sensors", "History", "Profile"]
