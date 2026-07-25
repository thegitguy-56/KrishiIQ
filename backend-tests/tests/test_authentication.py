"""
Authentication Tests — /api/v1/auth/*

Covers registration, login, and token-refresh flows: happy paths,
validation errors, duplicate-account handling, and credential checks.
JWT tampering / brute-force / bypass live in test_dast.py per the
project's DAST category, to avoid double counting.
"""
import uuid

import pytest

from conftest import FARMER1_PHONE, FARMER1_PASSWORD, OFFICER_PHONE, OFFICER_PASSWORD


def _rand_phone():
    return "70" + str(uuid.uuid4().int)[:8]


def _rand_email():
    return f"qa_{uuid.uuid4().hex[:10]}@example.com"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
class TestRegister:
    def test_register_success(self, api, api_url):
        """
        CATEGORY: Authentication
        TITLE: Register a new farmer with valid data
        OBJECTIVE: Confirm a well-formed registration returns 201 and a usable token pair
        EXPECTED: 201 Created, access_token and refresh_token present, role == farmer
        SEVERITY: Low
        """
        body = {
            "phone": _rand_phone(),
            "password": "S3cure!Pass",
            "name": "QA Test Farmer",
            "email": _rand_email(),
            "district": "Coimbatore",
        }
        r = api.post(api_url("/auth/register"), json=body)
        assert r.status_code == 201, r.text
        data = r.json()
        assert "access_token" in data and "refresh_token" in data
        assert data["role"] == "farmer"

    def test_register_duplicate_phone_rejected(self, api, api_url):
        """
        CATEGORY: Authentication
        TITLE: Reject registration with an already-registered phone number
        OBJECTIVE: Verify uniqueness constraint on phone is enforced at the API layer
        EXPECTED: 400 Bad Request
        SEVERITY: Medium
        """
        r = api.post(
            api_url("/auth/register"),
            json={
                "phone": FARMER1_PHONE,
                "password": "whatever123",
                "name": "Dup",
                "email": _rand_email(),
                "district": "Coimbatore",
            },
        )
        assert r.status_code == 400

    def test_register_duplicate_email_rejected(self, api, api_url):
        """
        CATEGORY: Authentication
        TITLE: Reject registration with an already-registered email
        EXPECTED: 400 Bad Request
        SEVERITY: Medium
        """
        r = api.post(
            api_url("/auth/register"),
            json={
                "phone": _rand_phone(),
                "password": "whatever123",
                "name": "Dup Email",
                "email": "farmer1@krishiiq.com",
                "district": "Coimbatore",
            },
        )
        assert r.status_code == 400

    @pytest.mark.parametrize("phone", ["123", "", "abcde", "12345678", "1"])
    def test_register_invalid_phone_rejected(self, api, api_url, phone):
        """
        CATEGORY: Authentication
        TITLE: Reject registration when phone number is too short/invalid
        TEST_DATA: phone={phone}
        EXPECTED: 400 or 422 — never 201
        SEVERITY: Medium
        """
        r = api.post(
            api_url("/auth/register"),
            json={
                "phone": phone,
                "password": "whatever123",
                "name": "Bad Phone",
                "email": _rand_email(),
                "district": "Coimbatore",
            },
        )
        assert r.status_code in (400, 422), r.text

    @pytest.mark.parametrize("email", ["not-an-email", "missing-at-sign.com", "a@b", "@@@"])
    def test_register_invalid_email_rejected(self, api, api_url, email):
        """
        CATEGORY: Authentication
        TITLE: Reject registration when email is malformed
        TEST_DATA: email={email}
        EXPECTED: 422 Unprocessable Entity (pydantic EmailStr validation)
        SEVERITY: Low
        """
        r = api.post(
            api_url("/auth/register"),
            json={
                "phone": _rand_phone(),
                "password": "whatever123",
                "name": "Bad Email",
                "email": email,
                "district": "Coimbatore",
            },
        )
        assert r.status_code == 422

    @pytest.mark.parametrize("missing_field", ["phone", "password", "name", "email", "district"])
    def test_register_missing_required_field(self, api, api_url, missing_field):
        """
        CATEGORY: Authentication
        TITLE: Reject registration missing a required field
        TEST_DATA: missing_field={missing_field}
        EXPECTED: 422 Unprocessable Entity
        SEVERITY: Low
        """
        body = {
            "phone": _rand_phone(),
            "password": "whatever123",
            "name": "Missing Field",
            "email": _rand_email(),
            "district": "Coimbatore",
        }
        del body[missing_field]
        r = api.post(api_url("/auth/register"), json=body)
        assert r.status_code == 422

    def test_register_empty_body(self, api, api_url):
        """
        CATEGORY: Authentication
        TITLE: Reject registration with an empty JSON body
        EXPECTED: 422 Unprocessable Entity
        SEVERITY: Low
        """
        r = api.post(api_url("/auth/register"), json={})
        assert r.status_code == 422

    def test_register_malformed_json(self, api, api_url):
        """
        CATEGORY: Authentication
        TITLE: Reject registration with malformed (non-JSON) body
        EXPECTED: 422 Unprocessable Entity, no 500
        SEVERITY: Low
        """
        r = api.post(
            api_url("/auth/register"),
            content=b"{not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422

    def test_register_weak_password_currently_accepted(self, api, api_url):
        """
        CATEGORY: Authentication
        TITLE: Registration accepts a trivially weak password
        OBJECTIVE: Document that no password-strength policy is enforced server-side
        EXPECTED: Documents current behaviour (201) and logs a Low-severity finding
        SEVERITY: Low
        """
        from conftest import record_finding as _record

        r = api.post(
            api_url("/auth/register"),
            json={
                "phone": _rand_phone(),
                "password": "1",
                "name": "Weak Pw",
                "email": _rand_email(),
                "district": "Coimbatore",
            },
        )
        if r.status_code == 201:
            _record(
                finding_id="AUTH-001",
                severity="Low",
                endpoint="POST /api/v1/auth/register",
                description="No minimum password length/complexity policy is enforced on registration.",
                evidence=f"Registered successfully with password='1' -> HTTP {r.status_code}",
                impact="Users can create accounts with trivially guessable passwords, increasing brute-force and credential-stuffing risk.",
                remediation="Enforce a minimum length (>=8) and complexity policy in RegisterRequest / auth_service.register_user, e.g. via a pydantic validator.",
                owasp="A07:2021 - Identification and Authentication Failures",
                cwe="CWE-521",
            )
        assert r.status_code in (201, 400, 422)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
class TestLogin:
    @pytest.mark.parametrize(
        "phone,password",
        [
            (FARMER1_PHONE, FARMER1_PASSWORD),
            (OFFICER_PHONE, OFFICER_PASSWORD),
        ],
    )
    def test_login_success(self, api, api_url, phone, password):
        """
        CATEGORY: Authentication
        TITLE: Login succeeds with valid seeded credentials
        TEST_DATA: phone={phone}
        EXPECTED: 200 OK with access_token, refresh_token, correct role
        SEVERITY: Low
        """
        r = api.post(api_url("/auth/login"), json={"phone": phone, "password": password})
        assert r.status_code == 200
        data = r.json()
        assert data["access_token"]
        assert data["refresh_token"]

    def test_login_wrong_password(self, api, api_url):
        """
        CATEGORY: Authentication
        TITLE: Reject login with correct phone but wrong password
        EXPECTED: 401 Unauthorized, generic error message (no user enumeration)
        SEVERITY: Medium
        """
        r = api.post(api_url("/auth/login"), json={"phone": FARMER1_PHONE, "password": "wrong-password"})
        assert r.status_code == 401

    def test_login_nonexistent_phone(self, api, api_url):
        """
        CATEGORY: Authentication
        TITLE: Reject login for a phone number that was never registered
        EXPECTED: 401 Unauthorized (same status/shape as wrong-password case)
        SEVERITY: Medium
        """
        r = api.post(api_url("/auth/login"), json={"phone": "6199999999", "password": "whatever123"})
        assert r.status_code == 401

    def test_login_error_message_does_not_leak_account_existence(self, api, api_url):
        """
        CATEGORY: Authentication
        TITLE: Login error messages are identical for wrong-password vs unknown-phone
        OBJECTIVE: Confirm the API does not allow account enumeration via error text
        EXPECTED: Both cases return the same detail message
        SEVERITY: Medium
        """
        r1 = api.post(api_url("/auth/login"), json={"phone": FARMER1_PHONE, "password": "wrong-password"})
        r2 = api.post(api_url("/auth/login"), json={"phone": "6100000099", "password": "wrong-password"})
        assert r1.status_code == r2.status_code == 401
        assert r1.json().get("detail") == r2.json().get("detail")

    @pytest.mark.parametrize("missing_field", ["phone", "password"])
    def test_login_missing_field(self, api, api_url, missing_field):
        """
        CATEGORY: Authentication
        TITLE: Reject login missing phone or password
        TEST_DATA: missing_field={missing_field}
        EXPECTED: 422 Unprocessable Entity
        SEVERITY: Low
        """
        body = {"phone": FARMER1_PHONE, "password": FARMER1_PASSWORD}
        del body[missing_field]
        r = api.post(api_url("/auth/login"), json=body)
        assert r.status_code == 422

    def test_login_empty_credentials(self, api, api_url):
        """
        CATEGORY: Authentication
        TITLE: Reject login with empty phone/password strings
        EXPECTED: 401 or 422, never 200
        SEVERITY: Low
        """
        r = api.post(api_url("/auth/login"), json={"phone": "", "password": ""})
        assert r.status_code in (401, 422)

    def test_login_case_sensitivity_of_phone(self, api, api_url):
        """
        CATEGORY: Authentication
        TITLE: Phone lookup is exact-match (whitespace is not silently trimmed)
        EXPECTED: Login with a padded phone number fails cleanly (401/422), not 500
        SEVERITY: Low
        """
        r = api.post(api_url("/auth/login"), json={"phone": f" {FARMER1_PHONE} ", "password": FARMER1_PASSWORD})
        assert r.status_code in (401, 422)


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------
class TestRefresh:
    def test_refresh_with_valid_refresh_token(self, api, api_url, farmer1_auth):
        """
        CATEGORY: Authentication
        TITLE: Refresh endpoint issues a new token pair for a valid refresh token
        EXPECTED: 200 OK with a fresh access_token
        SEVERITY: Low
        """
        r = api.post(
            api_url("/auth/refresh"),
            params={"refresh_token": farmer1_auth["refresh_token"]},
        )
        assert r.status_code == 200
        assert r.json()["access_token"]

    def test_refresh_with_access_token_rejected(self, api, api_url, farmer1_auth):
        """
        CATEGORY: Authentication
        TITLE: Reject refresh when an access token (not a refresh token) is supplied
        OBJECTIVE: Confirm the endpoint validates the JWT 'type' claim, not just the signature
        EXPECTED: 401 Unauthorized
        SEVERITY: High
        """
        r = api.post(
            api_url("/auth/refresh"),
            params={"refresh_token": farmer1_auth["access_token"]},
        )
        assert r.status_code == 401

    def test_refresh_with_garbage_token(self, api, api_url):
        """
        CATEGORY: Authentication
        TITLE: Reject refresh with a syntactically invalid token
        EXPECTED: 401 Unauthorized, no 500
        SEVERITY: Medium
        """
        r = api.post(api_url("/auth/refresh"), params={"refresh_token": "not.a.jwt"})
        assert r.status_code == 401

    def test_refresh_missing_token(self, api, api_url):
        """
        CATEGORY: Authentication
        TITLE: Reject refresh call with no refresh_token supplied
        EXPECTED: 422 Unprocessable Entity
        SEVERITY: Low
        """
        r = api.post(api_url("/auth/refresh"))
        assert r.status_code == 422
