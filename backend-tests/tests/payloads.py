"""
Shared malicious / boundary payload catalogs used by the injection,
input-validation, business-logic and DAST test modules.

Kept in one place so every test module attacks the SAME payload set,
which keeps the generated test-cases.xlsx consistent and makes it easy
to extend coverage by editing a single file.
"""

# ---------------------------------------------------------------------------
# SQL Injection
# ---------------------------------------------------------------------------
SQLI_PAYLOADS = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "'; DROP TABLE users;--",
    "' UNION SELECT NULL--",
    "1' AND SLEEP(3)--",
    "admin'--",
    "' OR 1=1#",
    "\" OR \"1\"=\"1",
]

# ---------------------------------------------------------------------------
# NoSQL Injection (defensive coverage even though the backend is relational —
# proves operator-injection strings are treated as inert data, not parsed)
# ---------------------------------------------------------------------------
NOSQLI_PAYLOADS = [
    '{"$ne": null}',
    '{"$gt": ""}',
    '{"$where": "1==1"}',
]

# ---------------------------------------------------------------------------
# OS Command Injection
# ---------------------------------------------------------------------------
CMD_INJECTION_PAYLOADS = [
    "; ls -la",
    "| whoami",
    "$(cat /etc/passwd)",
    "`id`",
    "&& cat /etc/shadow",
]

# ---------------------------------------------------------------------------
# Path Traversal
# ---------------------------------------------------------------------------
PATH_TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\win.ini",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "....//....//....//etc/passwd",
]

# ---------------------------------------------------------------------------
# XSS / stored-HTML
# ---------------------------------------------------------------------------
XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "\"><img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
]

# ---------------------------------------------------------------------------
# SSRF targets
# ---------------------------------------------------------------------------
SSRF_PAYLOADS = [
    "http://169.254.169.254/latest/meta-data/",
    "http://localhost:6379/",
    "file:///etc/passwd",
    "http://127.0.0.1:8000/api/v1/dashboard/overview",
]

# Combined pool used by the generic "fuzz every text field" tests.
ALL_INJECTION_PAYLOADS = (
    [("sqli", p) for p in SQLI_PAYLOADS]
    + [("nosqli", p) for p in NOSQLI_PAYLOADS]
    + [("cmd", p) for p in CMD_INJECTION_PAYLOADS]
    + [("path_traversal", p) for p in PATH_TRAVERSAL_PAYLOADS]
    + [("xss", p) for p in XSS_PAYLOADS]
)

# ---------------------------------------------------------------------------
# Boundary / malformed values for input-validation tests
# ---------------------------------------------------------------------------
BOUNDARY_STRINGS = [
    "",  # empty
    " ",  # whitespace only
    "A" * 10000,  # oversized
    "😀🌾🚜" * 50,  # unicode / emoji flood
    None,  # wrong type (will be sent as JSON null)
]

BOUNDARY_NUMBERS = [-1, 0, 999999999, -999999999, 0.0000001]

INVALID_UUIDS = [
    "not-a-uuid",
    "12345",
    "' OR '1'='1",
    "00000000-0000-0000-0000-000000000000",  # well-formed but non-existent
    "../../etc/passwd",
]
