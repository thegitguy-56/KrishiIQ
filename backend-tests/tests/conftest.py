"""
Shared fixtures for the KrishiIQ backend test suite, plus a lightweight
in-repo pytest plugin that turns every test's docstring into a row of the
structured test-case catalog (test-cases.xlsx) and collects security
findings (findings.xlsx) for the audit report.

The suite talks to a REAL running instance of the FastAPI app over HTTP —
it never imports the app in-process — so it exercises the exact same code
path as a real attacker / real client would (CORS middleware, JSON
parsing, auth dependency injection, DB round trips, etc).

Target server is controlled entirely by the API_BASE_URL environment
variable so the same suite can run against:
  - the ephemeral CI instance (default, safe, non-destructive)
  - a locally running instance (for the developer's own machine, optional)
  - the deployed Render instance (opt-in only, see README.md)
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import httpx
import pytest

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
API_PREFIX = "/api/v1"
REQUEST_TIMEOUT = float(os.environ.get("API_TIMEOUT", "20"))

# Seeded accounts created automatically by backend/app/main.py's _auto_seed()
# and backend/app/api/create_admin_officer.py — see README.md for how these
# are provisioned in CI (ephemeral SQLite DB, never real user data).
OFFICER_PHONE, OFFICER_PASSWORD = "9000000001", "officer123"
ADMIN_PHONE, ADMIN_PASSWORD = "9000000003", "admin123"
FARMER1_PHONE, FARMER1_PASSWORD = "9000000002", "farmer123"   # Coimbatore
FARMER2_PHONE, FARMER2_PASSWORD = "9100000001", "farmer123"   # Salem — used for IDOR/cross-tenant tests

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
ARTIFACT_DIR.mkdir(exist_ok=True)

_FINDINGS = []
_FINDING_IDS_SEEN = set()


def record_finding(
    finding_id: str,
    severity: str,
    endpoint: str,
    description: str,
    evidence: str,
    impact: str,
    remediation: str,
    owasp: str = "",
    cwe: str = "",
):
    """Called by tests to log a confirmed security finding for the report.

    Safe to call more than once for the same finding_id across a
    parametrized test — duplicates are collapsed.
    """
    key = (finding_id, endpoint)
    if key in _FINDING_IDS_SEEN:
        return
    _FINDING_IDS_SEEN.add(key)
    _FINDINGS.append(
        {
            "finding_id": finding_id,
            "severity": severity,
            "endpoint": endpoint,
            "description": description,
            "evidence": evidence,
            "impact": impact,
            "remediation": remediation,
            "owasp": owasp,
            "cwe": cwe,
        }
    )


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def base_url() -> str:
    return API_BASE_URL


@pytest.fixture(scope="session")
def api() -> httpx.Client:
    with httpx.Client(base_url=API_BASE_URL, timeout=REQUEST_TIMEOUT) as client:
        yield client


def _url(path: str) -> str:
    if path.startswith("/api/"):
        return path
    return f"{API_PREFIX}{path}"


@pytest.fixture(scope="session")
def api_url():
    return _url


# ---------------------------------------------------------------------------
# Server readiness (also used standalone by the CI workflow via -m wait)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _wait_for_server():
    deadline = time.time() + 60
    last_err = None
    while time.time() < deadline:
        try:
            r = httpx.get(f"{API_BASE_URL}/health", timeout=3)
            if r.status_code == 200:
                return
        except Exception as e:  # noqa: BLE001
            last_err = e
        time.sleep(1)
    pytest.exit(f"Backend at {API_BASE_URL} never became healthy: {last_err}")


# ---------------------------------------------------------------------------
# Auth token fixtures (session-scoped — one login per role per run)
# ---------------------------------------------------------------------------
def _login(api: httpx.Client, phone: str, password: str) -> dict:
    r = api.post(_url("/auth/login"), json={"phone": phone, "password": password})
    assert r.status_code == 200, f"Seed login failed for {phone}: {r.status_code} {r.text}"
    return r.json()


@pytest.fixture(scope="session")
def officer_auth(api):
    data = _login(api, OFFICER_PHONE, OFFICER_PASSWORD)
    return data


@pytest.fixture(scope="session")
def admin_auth(api):
    data = _login(api, ADMIN_PHONE, ADMIN_PASSWORD)
    return data


@pytest.fixture(scope="session")
def farmer1_auth(api):
    data = _login(api, FARMER1_PHONE, FARMER1_PASSWORD)
    return data


@pytest.fixture(scope="session")
def farmer2_auth(api):
    data = _login(api, FARMER2_PHONE, FARMER2_PASSWORD)
    return data


def _hdr(token_payload: dict) -> dict:
    return {"Authorization": f"Bearer {token_payload['access_token']}"}


@pytest.fixture(scope="session")
def officer_headers(officer_auth):
    return _hdr(officer_auth)


@pytest.fixture(scope="session")
def admin_headers(admin_auth):
    return _hdr(admin_auth)


@pytest.fixture(scope="session")
def farmer1_headers(farmer1_auth):
    return _hdr(farmer1_auth)


@pytest.fixture(scope="session")
def farmer2_headers(farmer2_auth):
    return _hdr(farmer2_auth)


@pytest.fixture(scope="session")
def farmer1_farm_id(api, farmer1_headers):
    r = api.get(_url("/farms/"), headers=farmer1_headers)
    assert r.status_code == 200
    farms = r.json()
    assert farms, "Seed data expected to give farmer1 at least one farm"
    return farms[0]["id"]


@pytest.fixture(scope="session")
def farmer2_farm_id(api, farmer2_headers):
    r = api.get(_url("/farms/"), headers=farmer2_headers)
    assert r.status_code == 200
    farms = r.json()
    assert farms, "Seed data expected to give farmer2 at least one farm"
    return farms[0]["id"]


# ---------------------------------------------------------------------------
# Test-case catalog plugin
# ---------------------------------------------------------------------------
_FIELD_RE = re.compile(
    r"^\s*(CATEGORY|TITLE|OBJECTIVE|PRECONDITIONS|STEPS|TEST_DATA|EXPECTED|SEVERITY)\s*:\s*(.*)$"
)

_CATEGORY_BY_FILE = [
    ("test_authentication", "Authentication"),
    ("test_authorization", "Authorization"),
    ("test_input_validation", "Input Validation"),
    ("test_injection", "Injection"),
    ("test_business_logic", "Business Logic"),
    ("test_configuration", "Configuration"),
    ("test_functional_api", "Functional API"),
    ("test_dast", "DAST"),
    ("test_performance", "Performance"),
]

_ITEM_META: dict[str, dict] = {}
_ITEM_OUTCOME: dict[str, str] = {}


def _parse_docstring(doc):
    data = {}
    if not doc:
        return data
    for line in doc.splitlines():
        m = _FIELD_RE.match(line)
        if m:
            data[m.group(1)] = m.group(2).strip()
    return data


def _infer_category(path: str) -> str:
    for key, cat in _CATEGORY_BY_FILE:
        if key in path:
            return cat
    return "General"


def pytest_collection_modifyitems(config, items):
    for idx, item in enumerate(items, start=1):
        doc = getattr(getattr(item, "function", None), "__doc__", None)
        meta = _parse_docstring(doc)
        test_data = meta.get("TEST_DATA", "")
        if not test_data and hasattr(item, "callspec"):
            try:
                test_data = json.dumps(item.callspec.params, default=str)[:500]
            except Exception:  # noqa: BLE001
                test_data = str(item.callspec.params)[:500]
        _ITEM_META[item.nodeid] = {
            "id": f"TC-{idx:04d}",
            "category": meta.get("CATEGORY", _infer_category(str(item.fspath))),
            "title": meta.get("TITLE", item.name),
            "objective": meta.get("OBJECTIVE", ""),
            "preconditions": meta.get("PRECONDITIONS", "Seeded demo accounts available; backend reachable"),
            "steps": meta.get("STEPS", "See test implementation in repository"),
            "test_data": test_data,
            "expected": meta.get("EXPECTED", ""),
            "severity": meta.get("SEVERITY", "Informational"),
            "nodeid": item.nodeid,
        }


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        _ITEM_OUTCOME[item.nodeid] = "Pass" if rep.passed else ("Fail" if rep.failed else "Skip")
    elif rep.when == "setup":
        if rep.skipped:
            _ITEM_OUTCOME.setdefault(item.nodeid, "Skip")
        elif not rep.passed:
            _ITEM_OUTCOME.setdefault(item.nodeid, "Error")


def pytest_sessionfinish(session, exitstatus):
    catalog = []
    for nodeid, meta in _ITEM_META.items():
        row = dict(meta)
        row["status"] = _ITEM_OUTCOME.get(nodeid, "Skip")
        catalog.append(row)
    (ARTIFACT_DIR / "test_catalog.json").write_text(json.dumps(catalog, indent=2))
    (ARTIFACT_DIR / "findings.json").write_text(json.dumps(_FINDINGS, indent=2))
    summary = {
        "total": len(catalog),
        "passed": sum(1 for c in catalog if c["status"] == "Pass"),
        "failed": sum(1 for c in catalog if c["status"] == "Fail"),
        "skipped": sum(1 for c in catalog if c["status"] == "Skip"),
        "error": sum(1 for c in catalog if c["status"] == "Error"),
        "findings_count": len(_FINDINGS),
        "target": API_BASE_URL,
    }
    (ARTIFACT_DIR / "run_summary.json").write_text(json.dumps(summary, indent=2))
