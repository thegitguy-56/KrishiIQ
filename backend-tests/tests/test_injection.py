"""
Injection Tests — SQL, NoSQL-style operator, OS command, path traversal,
XSS, and SSRF payloads fired at every text input the API accepts.

The backend uses SQLAlchemy ORM (parameterized queries) throughout, so
these tests are expected to PASS (payload treated as inert string data)
in the current codebase. They exist to catch regressions — e.g. a future
raw `text()` query or f-string SQL — and to give the audit report
concrete evidence that injection defenses were actually exercised rather
than assumed.
"""
import pytest

from payloads import ALL_INJECTION_PAYLOADS, SSRF_PAYLOADS


def _assert_safe_response(r, context: str):
    """A safe response to an injection attempt is any clean HTTP error or
    a 200/201 that stored the payload as literal data. A 500 (unhandled
    exception) or a response that echoes back SQL/DB error text is the
    signature of a real vulnerability and is treated as a failure.
    """
    assert r.status_code != 500, f"{context}: server error suggests unsanitized input reached a lower layer\n{r.text[:300]}"
    lowered = r.text.lower()
    for leak_marker in ("sqlite3.", "psycopg2.", "syntax error", "traceback (most recent", "sqlalchemy.exc"):
        assert leak_marker not in lowered, f"{context}: possible stack-trace / DB error leak: {leak_marker}"


class TestInjectionInAuthFields:
    @pytest.mark.parametrize("kind,payload", ALL_INJECTION_PAYLOADS)
    def test_login_phone_field_injection(self, api, api_url, kind, payload):
        """
        CATEGORY: Injection
        TITLE: Login 'phone' field resists injection payloads
        TEST_DATA: kind={kind}
        EXPECTED: 401/422, never 200 and never a raw DB/server error
        SEVERITY: Critical
        """
        r = api.post(api_url("/auth/login"), json={"phone": payload, "password": "whatever123"})
        _assert_safe_response(r, f"login.phone[{kind}]")
        assert r.status_code in (401, 422)

    @pytest.mark.parametrize("kind,payload", ALL_INJECTION_PAYLOADS)
    def test_register_name_field_injection(self, api, api_url, kind, payload):
        """
        CATEGORY: Injection
        TITLE: Register 'name' field resists injection payloads
        TEST_DATA: kind={kind}
        EXPECTED: 201/400/422, never 500
        SEVERITY: Critical
        """
        import uuid

        r = api.post(
            api_url("/auth/register"),
            json={
                "phone": "72" + str(uuid.uuid4().int)[:8],
                "password": "whatever123",
                "name": payload,
                "email": f"inj_{uuid.uuid4().hex[:8]}@example.com",
                "district": "Coimbatore",
            },
        )
        _assert_safe_response(r, f"register.name[{kind}]")

    @pytest.mark.parametrize("kind,payload", ALL_INJECTION_PAYLOADS)
    def test_register_district_field_injection(self, api, api_url, kind, payload):
        """
        CATEGORY: Injection
        TITLE: Register 'district' field resists injection payloads
        TEST_DATA: kind={kind}
        EXPECTED: 201/400/422, never 500
        SEVERITY: High
        """
        import uuid

        r = api.post(
            api_url("/auth/register"),
            json={
                "phone": "73" + str(uuid.uuid4().int)[:8],
                "password": "whatever123",
                "name": "Injection Test",
                "email": f"inj_{uuid.uuid4().hex[:8]}@example.com",
                "district": payload,
            },
        )
        _assert_safe_response(r, f"register.district[{kind}]")


class TestInjectionInFarmFields:
    @pytest.mark.parametrize("kind,payload", ALL_INJECTION_PAYLOADS)
    def test_farm_name_field_injection(self, api, api_url, farmer1_headers, kind, payload):
        """
        CATEGORY: Injection
        TITLE: Farm 'name' field resists injection payloads
        TEST_DATA: kind={kind}
        EXPECTED: 201/422, never 500; payload never executed
        SEVERITY: Critical
        """
        r = api.post(
            api_url("/farms/"),
            json={"name": payload, "area_acres": 1.0, "latitude": 11.0, "longitude": 76.9, "district": "Coimbatore"},
            headers=farmer1_headers,
        )
        _assert_safe_response(r, f"farm.name[{kind}]")
        if r.status_code == 201:
            assert r.json()["name"] == payload, "Stored value should equal input verbatim (no silent mutation/exec)"

    @pytest.mark.parametrize("kind,payload", ALL_INJECTION_PAYLOADS)
    def test_farm_soil_type_field_injection(self, api, api_url, farmer1_headers, kind, payload):
        """
        CATEGORY: Injection
        TITLE: Farm 'soil_type' field resists injection payloads
        TEST_DATA: kind={kind}
        EXPECTED: 201/422, never 500
        SEVERITY: High
        """
        r = api.post(
            api_url("/farms/"),
            json={
                "name": "Injection Farm",
                "area_acres": 1.0,
                "latitude": 11.0,
                "longitude": 76.9,
                "district": "Coimbatore",
                "soil_type": payload,
            },
            headers=farmer1_headers,
        )
        _assert_safe_response(r, f"farm.soil_type[{kind}]")

    @pytest.mark.parametrize("kind,payload", ALL_INJECTION_PAYLOADS)
    def test_farm_village_field_injection(self, api, api_url, farmer1_headers, kind, payload):
        """
        CATEGORY: Injection
        TITLE: Farm 'village' field resists injection payloads
        TEST_DATA: kind={kind}
        EXPECTED: 201/422, never 500
        SEVERITY: Medium
        """
        r = api.post(
            api_url("/farms/"),
            json={
                "name": "Injection Farm 2",
                "area_acres": 1.0,
                "latitude": 11.0,
                "longitude": 76.9,
                "district": "Coimbatore",
                "village": payload,
            },
            headers=farmer1_headers,
        )
        _assert_safe_response(r, f"farm.village[{kind}]")


class TestInjectionInCropFields:
    @pytest.mark.parametrize("kind,payload", ALL_INJECTION_PAYLOADS)
    def test_crop_name_field_injection(self, api, api_url, farmer1_headers, farmer1_farm_id, kind, payload):
        """
        CATEGORY: Injection
        TITLE: Crop 'crop_name' field resists injection payloads
        TEST_DATA: kind={kind}
        EXPECTED: 201/422, never 500
        SEVERITY: High
        """
        r = api.post(
            api_url("/crops"),
            json={"farm_id": farmer1_farm_id, "crop_name": payload, "season": "kharif", "area_acres": 1.0},
            headers=farmer1_headers,
        )
        _assert_safe_response(r, f"crop.crop_name[{kind}]")


class TestInjectionInQueryParams:
    @pytest.mark.parametrize("kind,payload", ALL_INJECTION_PAYLOADS)
    def test_dashboard_district_query_injection(self, api, api_url, officer_headers, kind, payload):
        """
        CATEGORY: Injection
        TITLE: Dashboard 'district' query param resists injection payloads
        TEST_DATA: kind={kind}
        EXPECTED: 200 with empty/safe results, never 500
        SEVERITY: High
        """
        r = api.get(api_url("/dashboard/overview"), params={"district": payload}, headers=officer_headers)
        _assert_safe_response(r, f"dashboard.district[{kind}]")
        assert r.status_code == 200

    @pytest.mark.parametrize("kind,payload", ALL_INJECTION_PAYLOADS)
    def test_disease_alerts_district_path_injection(self, api, api_url, farmer1_headers, kind, payload):
        """
        CATEGORY: Injection
        TITLE: Disease alerts '{{district}}' path param resists injection payloads
        TEST_DATA: kind={kind}
        EXPECTED: 200/404, never 500
        SEVERITY: High
        """
        import urllib.parse

        r = api.get(
            api_url(f"/disease/alerts/district/{urllib.parse.quote(payload, safe='')}"),
            headers=farmer1_headers,
        )
        _assert_safe_response(r, f"disease.alerts.district[{kind}]")


class TestSSRFResistance:
    @pytest.mark.parametrize("payload", SSRF_PAYLOADS)
    def test_weather_forecast_does_not_allow_ssrf_via_coordinates(self, api, api_url, farmer1_headers, payload):
        """
        CATEGORY: Injection
        TITLE: Weather forecast lat/lon params cannot be used for SSRF (they are typed floats)
        TEST_DATA: payload={payload}
        OBJECTIVE: Confirm lat/lon are strictly typed floats so no URL can be smuggled in
        EXPECTED: 422 Unprocessable Entity (type coercion failure)
        SEVERITY: Medium
        """
        r = api.get(api_url("/weather/forecast"), params={"lat": payload, "lon": 76.9}, headers=farmer1_headers)
        assert r.status_code == 422

    def test_farm_geojson_field_does_not_trigger_outbound_fetch(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Injection
        TITLE: Farm 'geojson' (Any type) field does not trigger server-side URL fetching
        TEST_DATA: geojson containing an internal metadata URL
        EXPECTED: 201/422, request completes quickly (no server-side HTTP fetch of the embedded URL)
        SEVERITY: Medium
        """
        import time

        start = time.time()
        r = api.post(
            api_url("/farms/"),
            json={
                "name": "SSRF Probe Farm",
                "area_acres": 1.0,
                "latitude": 11.0,
                "longitude": 76.9,
                "district": "Coimbatore",
                "geojson": {"url": "http://169.254.169.254/latest/meta-data/"},
            },
            headers=farmer1_headers,
        )
        elapsed = time.time() - start
        assert r.status_code != 500
        assert elapsed < 10, "Unexpectedly slow response may indicate a server-side outbound fetch attempt (SSRF)"
