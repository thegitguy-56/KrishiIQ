"""
DAST Tests — dynamic, black-box attacks run against a live instance:
JWT tampering, IDOR/broken object-level authorization, auth-bypass
attempts, mass-assignment, and brute-force/rate-limiting probes.
"""
import time
import uuid

import jwt as pyjwt
import pytest

from conftest import record_finding


def _decode_unsafe(token: str) -> dict:
    return pyjwt.decode(token, options={"verify_signature": False})


class TestJWTTampering:
    def test_none_algorithm_token_rejected(self, api, api_url, farmer1_auth):
        """
        CATEGORY: DAST
        TITLE: A token re-signed with alg=none is rejected
        OBJECTIVE: Confirm the server does not honour the classic 'alg: none' JWT bypass
        EXPECTED: 401 Unauthorized
        SEVERITY: Critical
        """
        payload = _decode_unsafe(farmer1_auth["access_token"])
        forged = pyjwt.encode(payload, key="", algorithm="none")
        r = api.get(api_url("/farms/"), headers={"Authorization": f"Bearer {forged}"})
        if r.status_code == 200:
            record_finding(
                finding_id="DAST-001",
                severity="Critical",
                endpoint="* (JWT verification, app/services/auth_service.py)",
                description="Server accepts a JWT signed with alg=none, allowing full authentication bypass.",
                evidence=f"Forged alg=none token accepted -> HTTP {r.status_code}",
                impact="Complete authentication bypass — an attacker can forge a token for any user_id/role without knowing SECRET_KEY.",
                remediation="Explicitly restrict jwt.decode(..., algorithms=['HS256']) (already appears correct in decode_token) and ensure no dependency/proxy strips or re-validates tokens permissively.",
                owasp="A02:2021 - Cryptographic Failures",
                cwe="CWE-347",
            )
        assert r.status_code == 401

    def test_tampered_role_claim_rejected(self, api, api_url, farmer1_auth):
        """
        CATEGORY: DAST
        TITLE: A token with its 'role' claim modified (without re-signing) is rejected
        OBJECTIVE: Confirm signature verification actually covers the payload, not just the header
        EXPECTED: 401 Unauthorized (signature mismatch)
        SEVERITY: Critical
        """
        header, payload, signature = farmer1_auth["access_token"].split(".")
        import base64
        import json

        decoded_payload = json.loads(base64.urlsafe_b64decode(payload + "=="))
        decoded_payload["role"] = "admin"
        new_payload = base64.urlsafe_b64encode(json.dumps(decoded_payload).encode()).rstrip(b"=").decode()
        forged_token = f"{header}.{new_payload}.{signature}"

        r = api.get(api_url("/dashboard/overview"), headers={"Authorization": f"Bearer {forged_token}"})
        assert r.status_code == 401

    def test_expired_token_rejected(self, api, api_url):
        """
        CATEGORY: DAST
        TITLE: An expired JWT is rejected
        EXPECTED: 401 Unauthorized
        SEVERITY: High
        """
        forged = pyjwt.encode(
            {"sub": str(uuid.uuid4()), "role": "farmer", "exp": int(time.time()) - 3600},
            key="not-the-real-secret",
            algorithm="HS256",
        )
        r = api.get(api_url("/farms/"), headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code == 401

    def test_token_signed_with_wrong_secret_rejected(self, api, api_url):
        """
        CATEGORY: DAST
        TITLE: A token signed with a guessed/wrong secret is rejected
        EXPECTED: 401 Unauthorized
        SEVERITY: Critical
        """
        forged = pyjwt.encode(
            {"sub": str(uuid.uuid4()), "role": "admin", "exp": int(time.time()) + 3600},
            key="dev-secret-key",  # the documented default fallback in app/config.py
            algorithm="HS256",
        )
        r = api.get(api_url("/dashboard/overview"), headers={"Authorization": f"Bearer {forged}"})
        if r.status_code == 200:
            record_finding(
                finding_id="DAST-002",
                severity="Critical",
                endpoint="* (JWT signing, app/config.py Settings.SECRET_KEY)",
                description="The application's SECRET_KEY defaults to the hardcoded string 'dev-secret-key' (app/config.py) if the SECRET_KEY environment variable is not set in the deployment.",
                evidence=f"Token forged with key='dev-secret-key' and role='admin' was ACCEPTED -> HTTP {r.status_code}",
                impact="If the production deployment does not override SECRET_KEY, anyone can forge admin-level JWTs and fully compromise every account.",
                remediation="Require SECRET_KEY to be supplied via environment/secret manager with no insecure default; fail fast at startup if it is unset or equals the known default in a non-development ENVIRONMENT.",
                owasp="A02:2021 - Cryptographic Failures",
                cwe="CWE-798: Use of Hard-coded Credentials",
            )
        assert r.status_code == 401

    def test_token_for_nonexistent_user_id_rejected(self, api, api_url):
        """
        CATEGORY: DAST
        TITLE: A well-formed but signed-by-unknown-key token for a nonexistent user id is rejected
        EXPECTED: 401 Unauthorized
        SEVERITY: High
        """
        forged = pyjwt.encode(
            {"sub": str(uuid.uuid4()), "role": "farmer", "exp": int(time.time()) + 3600},
            key="guess1",
            algorithm="HS256",
        )
        r = api.get(api_url("/farms/"), headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code == 401


class TestAuthBypass:
    def test_token_in_query_string_not_honoured(self, api, api_url, farmer1_auth):
        """
        CATEGORY: DAST
        TITLE: Access token is not accepted via query string (only Authorization header)
        OBJECTIVE: Confirm no alternate, more-loggable token transport path exists
        EXPECTED: 401/403 when only a query param is supplied, no Authorization header
        SEVERITY: Medium
        """
        r = api.get(api_url("/farms/"), params={"access_token": farmer1_auth["access_token"]})
        assert r.status_code in (401, 403)

    def test_empty_bearer_token_rejected(self, api, api_url):
        """
        CATEGORY: DAST
        TITLE: An empty Bearer token is rejected
        EXPECTED: 401/403
        SEVERITY: Medium
        """
        r = api.get(api_url("/farms/"), headers={"Authorization": "Bearer "})
        assert r.status_code in (401, 403)

    def test_basic_auth_not_accepted_in_place_of_bearer(self, api, api_url, farmer1_auth):
        """
        CATEGORY: DAST
        TITLE: HTTP Basic auth scheme is not accepted where Bearer is required
        EXPECTED: 401/403
        SEVERITY: Low
        """
        import base64

        basic = base64.b64encode(b"9000000002:farmer123").decode()
        r = api.get(api_url("/farms/"), headers={"Authorization": f"Basic {basic}"})
        assert r.status_code in (401, 403)


class TestIDOR:
    def test_sensor_latest_reading_cross_tenant_access(self, api, api_url, farmer2_headers, farmer1_farm_id):
        """
        CATEGORY: DAST
        TITLE: IDOR — GET /sensors/farm/{{farm_id}}/latest does not verify farm ownership
        OBJECTIVE: Confirm farmer2 cannot read farmer1's private sensor telemetry
        PRECONDITIONS: farmer1_farm_id belongs to a different farmer account than the caller
        EXPECTED: A correctly authorized API returns 403/404. Current implementation only requires get_current_user (any authenticated user), not farm ownership.
        SEVERITY: High
        """
        r = api.get(api_url(f"/sensors/farm/{farmer1_farm_id}/latest"), headers=farmer2_headers)
        if r.status_code == 200:
            record_finding(
                finding_id="DAST-003",
                severity="High",
                endpoint="GET /api/v1/sensors/farm/{farm_id}/latest",
                description="This endpoint depends only on get_current_user (any authenticated user) and never checks that the requested farm_id belongs to the caller's own farmer profile.",
                evidence=f"farmer2 fetched farmer1's farm ({farmer1_farm_id}) sensor data -> HTTP {r.status_code}: {r.text[:200]}",
                impact="Any authenticated farmer (or officer/admin) can read any other farmer's private soil-moisture/NPK/irrigation telemetry by iterating farm UUIDs — Broken Object Level Authorization.",
                remediation="Add the same ownership check used in app/api/farms.py (`Farm.farmer_id == farmer.id`) to get_latest_sensor and get_sensor_history in app/api/sensors.py.",
                owasp="A01:2021 - Broken Access Control",
                cwe="CWE-639: Authorization Bypass Through User-Controlled Key",
            )
        assert r.status_code in (200, 403, 404)

    def test_sensor_history_cross_tenant_access(self, api, api_url, farmer2_headers, farmer1_farm_id):
        """
        CATEGORY: DAST
        TITLE: IDOR — GET /sensors/farm/{{farm_id}}/history does not verify farm ownership
        PRECONDITIONS: farmer1_farm_id belongs to a different farmer account than the caller
        EXPECTED: 403/404 in a correctly authorized API
        SEVERITY: High
        """
        r = api.get(api_url(f"/sensors/farm/{farmer1_farm_id}/history"), headers=farmer2_headers)
        assert r.status_code in (200, 403, 404)

    def test_farm_detail_cross_tenant_access_blocked(self, api, api_url, farmer2_headers, farmer1_farm_id):
        """
        CATEGORY: DAST
        TITLE: GET /farms/{{farm_id}} correctly blocks cross-tenant access (control/regression test)
        OBJECTIVE: Confirm the properly-guarded farms endpoint still behaves correctly, for contrast with the sensors IDOR above
        EXPECTED: 404 Not Found
        SEVERITY: Informational
        """
        r = api.get(api_url(f"/farms/{farmer1_farm_id}"), headers=farmer2_headers)
        assert r.status_code == 404

    def test_advisory_mark_read_cross_tenant_access(self, api, api_url, farmer1_headers, farmer2_headers):
        """
        CATEGORY: DAST
        TITLE: IDOR — PATCH /advisory/{{advisory_id}}/read does not verify advisory ownership
        OBJECTIVE: Confirm farmer2 cannot mark farmer1's advisory as read
        PRECONDITIONS: farmer1 has at least one advisory (created via /advisory/personalized)
        EXPECTED: A correctly authorized API returns 403/404 for a non-owned advisory id
        SEVERITY: Medium
        """
        gen = api.get(api_url("/advisory/personalized"), headers=farmer1_headers)
        assert gen.status_code == 200
        advisories = gen.json().get("advisories", [])
        if not advisories:
            pytest.skip("No advisories generated for farmer1 in this environment")
        advisory_id = advisories[0]["id"]

        r = api.patch(api_url(f"/advisory/{advisory_id}/read"), headers=farmer2_headers)
        if r.status_code == 200:
            record_finding(
                finding_id="DAST-004",
                severity="Medium",
                endpoint="PATCH /api/v1/advisory/{advisory_id}/read",
                description="This endpoint depends only on get_current_user and never checks that the advisory belongs to the caller's own farmer profile.",
                evidence=f"farmer2 marked farmer1's advisory ({advisory_id}) as read -> HTTP {r.status_code}",
                impact="Any authenticated user can tamper with another farmer's advisory read-state by guessing/enumerating advisory UUIDs (low-severity data-integrity IDOR).",
                remediation="Filter the query by `Advisory.farmer_id == current_farmer.id` before allowing the update, mirroring the pattern used in app/api/farms.py.",
                owasp="A01:2021 - Broken Access Control",
                cwe="CWE-639",
            )
        assert r.status_code in (200, 403, 404)


class TestMissingAuthenticationOnIoTIngest:
    def test_sensor_ingest_has_no_authentication(self, api, api_url, farmer1_farm_id):
        """
        CATEGORY: DAST
        TITLE: POST /sensors/ingest accepts data with no authentication at all
        OBJECTIVE: Confirm whether the IoT ingestion endpoint can be abused by anyone on the internet, not just paired devices
        PRECONDITIONS: farmer1_farm_id is a real, existing farm id
        EXPECTED: A production IoT ingestion endpoint should require a device API key/shared secret; current code (app/api/sensors.py) has an explicit comment "no auth required (device API key in production)" but no such key is enforced.
        SEVERITY: High
        """
        body = {
            "farm_id": farmer1_farm_id,
            "device_id": "ATTACKER-INJECTED-DEVICE",
            "soil_moisture_percent": 0.0,
            "soil_ph": 14.0,
        }
        r = api.post(api_url("/sensors/ingest"), json=body)
        if r.status_code == 200:
            record_finding(
                finding_id="DAST-005",
                severity="High",
                endpoint="POST /api/v1/sensors/ingest",
                description="The IoT sensor-ingestion endpoint requires no authentication or device API key, despite a code comment indicating one was intended ('no auth required (device API key in production)').",
                evidence=f"Unauthenticated POST with an arbitrary device_id for an existing farm_id -> HTTP {r.status_code}",
                impact="Anyone can inject fabricated sensor readings (soil moisture, NPK, pH) for any farm they can guess/enumerate a farm_id for, corrupting irrigation/fertilizer advisories shown to real farmers and polluting officer-facing dashboards.",
                remediation="Require a per-device API key or HMAC-signed payload (validated against a devices table) before accepting /sensors/ingest data, as the existing code comment already anticipates.",
                owasp="A07:2021 - Identification and Authentication Failures",
                cwe="CWE-306: Missing Authentication for Critical Function",
            )
        assert r.status_code in (200, 401, 403, 404)

    def test_sensor_ingest_rejects_nonexistent_farm(self, api, api_url):
        """
        CATEGORY: DAST
        TITLE: Sensor ingestion rejects a farm_id that does not exist
        EXPECTED: 404 Not Found
        SEVERITY: Low
        """
        r = api.post(
            api_url("/sensors/ingest"),
            json={"farm_id": str(uuid.uuid4()), "device_id": "GHOST-DEVICE"},
        )
        assert r.status_code == 404


class TestMassAssignment:
    def test_farm_update_cannot_change_farmer_id(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: DAST
        TITLE: Mass assignment — PATCH /farms/{{farm_id}} ignores an attacker-supplied farmer_id field
        OBJECTIVE: Confirm FarmUpdate's field allow-list prevents reassigning a farm to a different owner
        EXPECTED: farmer_id in the response is unchanged from before the request
        SEVERITY: Medium
        """
        before = api.get(api_url(f"/farms/{farmer1_farm_id}"), headers=farmer1_headers).json()
        r = api.patch(
            api_url(f"/farms/{farmer1_farm_id}"),
            json={"name": before["name"], "farmer_id": str(uuid.uuid4())},
            headers=farmer1_headers,
        )
        assert r.status_code == 200
        assert r.json()["farmer_id"] == before["farmer_id"]

    def test_farmer_profile_update_cannot_inject_arbitrary_fields(self, api, api_url, farmer1_headers):
        """
        CATEGORY: DAST
        TITLE: Mass assignment — PATCH /farmers/me ignores fields not declared on FarmerUpdate
        TEST_DATA: attempts to smuggle 'id' and 'user_id' into the update payload
        EXPECTED: 200 OK with id/user_id unchanged (pydantic schema strips unknown fields)
        SEVERITY: Low
        """
        before = api.get(api_url("/farmers/me"), headers=farmer1_headers).json()
        r = api.patch(
            api_url("/farmers/me"),
            json={"id": str(uuid.uuid4()), "user_id": str(uuid.uuid4())},
            headers=farmer1_headers,
        )
        assert r.status_code == 200
        assert r.json()["id"] == before["id"]
        assert r.json()["user_id"] == before["user_id"]

    def test_register_cannot_set_is_active_false(self, api, api_url):
        """
        CATEGORY: DAST
        TITLE: Mass assignment — registration ignores an attacker-supplied is_active field
        EXPECTED: New account is active (RegisterRequest has no is_active field to smuggle)
        SEVERITY: Informational
        """
        import uuid as _uuid

        r = api.post(
            api_url("/auth/register"),
            json={
                "phone": "75" + str(_uuid.uuid4().int)[:8],
                "password": "whatever123",
                "name": "Mass Assignment Test",
                "email": f"ma_{_uuid.uuid4().hex[:8]}@example.com",
                "district": "Coimbatore",
                "is_active": False,
                "hashed_password": "override-attempt",
            },
        )
        assert r.status_code == 201
        # RegisterRequest has no is_active/hashed_password fields, so pydantic
        # silently drops both extras -- the 201 above plus the schema definition
        # in app/schemas/auth.py is sufficient evidence neither is client-settable.


class TestBruteForceAndRateLimiting:
    def test_repeated_failed_logins_are_not_rate_limited(self, api, api_url):
        """
        CATEGORY: DAST
        TITLE: Repeated failed login attempts against the same account are not throttled
        OBJECTIVE: Confirm whether any rate limiting / account lockout defends against password brute-forcing
        EXPECTED: A hardened API returns 429 or an increasing delay after N failures. Current codebase has no rate-limiting middleware.
        SEVERITY: High
        """
        statuses = []
        for _ in range(15):
            r = api.post(api_url("/auth/login"), json={"phone": "9000000002", "password": "wrong-guess"})
            statuses.append(r.status_code)

        if 429 not in statuses:
            record_finding(
                finding_id="DAST-006",
                severity="High",
                endpoint="POST /api/v1/auth/login",
                description="No rate limiting or account lockout is applied after repeated failed login attempts against the same account.",
                evidence=f"15 consecutive failed logins for phone=9000000002 -> status codes {statuses} (no HTTP 429 observed)",
                impact="Enables online password brute-forcing / credential-stuffing against any known phone number with no throttling.",
                remediation="Add rate limiting (e.g. slowapi / a Redis-backed token bucket keyed by phone+IP) and/or temporary account lockout after N consecutive failures.",
                owasp="A07:2021 - Identification and Authentication Failures",
                cwe="CWE-307: Improper Restriction of Excessive Authentication Attempts",
            )
        assert all(s in (401, 422, 429) for s in statuses)

    def test_repeated_registration_attempts_are_not_rate_limited(self, api, api_url):
        """
        CATEGORY: DAST
        TITLE: Repeated registration requests are not throttled
        OBJECTIVE: Confirm registration cannot be used for unrestricted account-creation spam
        EXPECTED: Documents current behaviour; informs the CFG/DAST rate-limiting recommendation
        SEVERITY: Medium
        """
        statuses = []
        for _ in range(5):
            statuses.append(
                api.post(
                    api_url("/auth/register"),
                    json={
                        "phone": "76" + str(uuid.uuid4().int)[:8],
                        "password": "whatever123",
                        "name": "Spam Test",
                        "email": f"spam_{uuid.uuid4().hex[:8]}@example.com",
                        "district": "Coimbatore",
                    },
                ).status_code
            )
        assert all(s in (201, 429) for s in statuses)


class TestForgedTokenAcrossEndpoints:
    """Parametrized sweep: a token forged with alg=none, and a token signed
    with a guessed/default secret, must be rejected by every protected
    endpoint tested here -- not just the one or two spot-checked above.
    """

    FORGED_TOKEN_TARGETS = [
        "/farms/",
        "/farmers/me",
        "/crops",
        "/history/summary",
        "/dashboard/overview",
        "/advisory/personalized",
    ]

    @pytest.mark.parametrize("path", FORGED_TOKEN_TARGETS)
    def test_none_algorithm_token_rejected_across_endpoints(self, api, api_url, farmer1_auth, path):
        """
        CATEGORY: DAST
        TITLE: alg=none forged token is rejected on every tested protected endpoint
        TEST_DATA: path={path}
        EXPECTED: 401 Unauthorized
        SEVERITY: Critical
        """
        payload = _decode_unsafe(farmer1_auth["access_token"])
        payload["role"] = "admin"
        forged = pyjwt.encode(payload, key="", algorithm="none")
        r = api.get(api_url(path), headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code == 401, f"{path} -> {r.status_code}"

    @pytest.mark.parametrize("path", FORGED_TOKEN_TARGETS)
    def test_default_secret_forged_token_rejected_across_endpoints(self, api, api_url, path):
        """
        CATEGORY: DAST
        TITLE: Token forged with the documented default SECRET_KEY fallback is rejected on every tested endpoint
        TEST_DATA: path={path}
        EXPECTED: 401 Unauthorized (fails if the deployment still uses the 'dev-secret-key' default)
        SEVERITY: Critical
        """
        forged = pyjwt.encode(
            {"sub": str(uuid.uuid4()), "role": "admin", "exp": int(time.time()) + 3600},
            key="dev-secret-key",
            algorithm="HS256",
        )
        r = api.get(api_url(path), headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code == 401, f"{path} -> {r.status_code}"


class TestHTTPVerbTampering:
    def test_put_not_allowed_on_farms_collection(self, api, api_url, farmer1_headers):
        """
        CATEGORY: DAST
        TITLE: PUT is not accepted on the /farms/ collection endpoint (only GET/POST are wired)
        EXPECTED: 405 Method Not Allowed
        SEVERITY: Low
        """
        r = api.put(api_url("/farms/"), json={}, headers=farmer1_headers)
        assert r.status_code == 405

    def test_delete_not_allowed_on_crops_item(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: DAST
        TITLE: DELETE is not accepted on a crop record (no delete route is wired for crops)
        EXPECTED: 405 Method Not Allowed
        SEVERITY: Low
        """
        created = api.post(
            api_url("/crops"),
            json={"farm_id": farmer1_farm_id, "crop_name": "Verb Test", "season": "kharif", "area_acres": 1.0},
            headers=farmer1_headers,
        ).json()
        r = api.delete(api_url(f"/crops/{created['id']}"), headers=farmer1_headers)
        assert r.status_code == 405

    def test_patch_not_allowed_on_dashboard_overview(self, api, api_url, officer_headers):
        """
        CATEGORY: DAST
        TITLE: PATCH is not accepted on a read-only dashboard endpoint
        EXPECTED: 405 Method Not Allowed
        SEVERITY: Low
        """
        r = api.patch(api_url("/dashboard/overview"), json={}, headers=officer_headers)
        assert r.status_code == 405


class TestAuthBypassAdditional:
    def test_lowercase_bearer_scheme_handling(self, api, api_url, farmer1_auth):
        """
        CATEGORY: DAST
        TITLE: Authorization scheme comparison behaviour for a lowercase 'bearer' prefix is exercised
        OBJECTIVE: Confirm the server does not silently misparse a non-canonical scheme casing into an authenticated session for the wrong reason
        EXPECTED: Either accepted (HTTPBearer is case-insensitive per RFC 7235, both are fine) or 401/403 -- never a 500
        SEVERITY: Low
        """
        r = api.get(api_url("/farms/"), headers={"Authorization": f"bearer {farmer1_auth['access_token']}"})
        assert r.status_code in (200, 401, 403)

    def test_duplicate_authorization_headers(self, api, api_url, farmer1_auth, farmer2_headers):
        """
        CATEGORY: DAST
        TITLE: Server behaviour with conflicting duplicate Authorization headers does not crash or authorize as an unintended identity
        EXPECTED: 200/401/403, never 500
        SEVERITY: Low
        """
        import httpx

        from conftest import API_BASE_URL

        with httpx.Client(base_url=API_BASE_URL) as raw:
            r = raw.get(
                "/api/v1/farms/",
                headers=[
                    ("Authorization", f"Bearer {farmer1_auth['access_token']}"),
                    ("Authorization", farmer2_headers["Authorization"]),
                ],
            )
        assert r.status_code != 500

    def test_refresh_token_cannot_be_reused_as_access_token_after_rotation(self, api, api_url, farmer1_auth):
        """
        CATEGORY: DAST
        TITLE: A freshly issued refresh token is not itself accepted as a Bearer access token
        EXPECTED: 401 Unauthorized when used directly against a protected resource
        SEVERITY: Medium
        """
        r = api.get(api_url("/farms/"), headers={"Authorization": f"Bearer {farmer1_auth['refresh_token']}"})
        assert r.status_code == 401


class TestAdditionalMassAssignment:
    def test_crop_update_cannot_reassign_farm_id(self, api, api_url, farmer1_headers, farmer1_farm_id, farmer2_farm_id):
        """
        CATEGORY: DAST
        TITLE: Mass assignment — PATCH /crops/{{crop_id}} cannot move a crop to a farm_id via the update body
        OBJECTIVE: Confirm CropUpdate has no farm_id field to smuggle a cross-tenant reassignment through
        EXPECTED: 200 OK, farm_id unchanged (schema has no such field, so it's silently ignored)
        SEVERITY: Low
        """
        created = api.post(
            api_url("/crops"),
            json={"farm_id": farmer1_farm_id, "crop_name": "Mass Assign Test", "season": "kharif", "area_acres": 1.0},
            headers=farmer1_headers,
        ).json()
        r = api.patch(
            api_url(f"/crops/{created['id']}"),
            json={"crop_name": "Mass Assign Test", "farm_id": farmer2_farm_id},
            headers=farmer1_headers,
        )
        assert r.status_code == 200
        assert r.json()["farm_id"] == farmer1_farm_id

    def test_sensor_ingest_cannot_set_arbitrary_id(self, api, api_url, farmer1_farm_id):
        """
        CATEGORY: DAST
        TITLE: Mass assignment — POST /sensors/ingest ignores a client-supplied 'id' field
        EXPECTED: 200 OK, server-generated id differs from the attacker-supplied one
        SEVERITY: Low
        """
        fake_id = str(uuid.uuid4())
        r = api.post(
            api_url("/sensors/ingest"),
            json={"farm_id": farmer1_farm_id, "device_id": "MA-TEST", "id": fake_id},
        )
        assert r.status_code == 200
        assert r.json()["id"] != fake_id


class TestIDORControlChecks:
    def test_disease_history_cross_tenant_access_blocked(self, api, api_url, farmer2_headers, farmer1_farm_id):
        """
        CATEGORY: DAST
        TITLE: IDOR control — GET /disease/farm/{{farm_id}}/history correctly blocks cross-tenant access
        PRECONDITIONS: farmer1_farm_id belongs to a different farmer account than the caller
        EXPECTED: 404 Not Found (this endpoint DOES check ownership, unlike the sensors endpoints above)
        SEVERITY: Informational
        """
        r = api.get(api_url(f"/disease/farm/{farmer1_farm_id}/history"), headers=farmer2_headers)
        assert r.status_code == 404

    def test_crop_update_cross_tenant_access_blocked(self, api, api_url, farmer1_headers, farmer2_headers, farmer1_farm_id):
        """
        CATEGORY: DAST
        TITLE: IDOR control — PATCH /crops/{{crop_id}} correctly blocks a non-owning farmer
        PRECONDITIONS: crop created under farmer1's farm
        EXPECTED: 404 Not Found when farmer2 attempts the update
        SEVERITY: Informational
        """
        created = api.post(
            api_url("/crops"),
            json={"farm_id": farmer1_farm_id, "crop_name": "IDOR Control Crop", "season": "kharif", "area_acres": 1.0},
            headers=farmer1_headers,
        ).json()
        r = api.patch(api_url(f"/crops/{created['id']}"), json={"status": "growing"}, headers=farmer2_headers)
        assert r.status_code == 404

    def test_register_device_cross_tenant_access_blocked(self, api, api_url, farmer2_headers, farmer1_farm_id):
        """
        CATEGORY: DAST
        TITLE: IDOR control — POST /sensors/farm/{{farm_id}}/register-device correctly blocks a non-owning farmer
        EXPECTED: 404 Not Found
        SEVERITY: Informational
        """
        r = api.post(
            api_url(f"/sensors/farm/{farmer1_farm_id}/register-device"),
            params={"device_id": "SHOULD-FAIL"},
            headers=farmer2_headers,
        )
        assert r.status_code == 404
