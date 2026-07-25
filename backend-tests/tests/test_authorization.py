"""
Authorization Tests — role-based access control (require_farmer /
require_officer / require_admin) across every protected endpoint.

Confirms:
  1. Unauthenticated requests are rejected (401) on every protected route.
  2. Requests from a wrong-role account are rejected (403) on every
     role-restricted route.
"""
import pytest

# Officer/admin-only endpoints (require_officer)
OFFICER_ONLY_GET_ENDPOINTS = [
    "/dashboard/overview",
    "/dashboard/district-heatmap",
    "/dashboard/farmers",
    "/dashboard/farms-map",
    "/dashboard/crop-distribution",
    "/dashboard/yield-trends",
    "/dashboard/districts",
    "/dashboard/water-usage",
]

# Farmer-only endpoints (require_farmer), GET method
FARMER_ONLY_GET_ENDPOINTS = [
    "/farms/",
    "/farmers/me",
    "/history/summary",
    "/history/crops",
    "/history/diseases",
    "/advisory/personalized",
]

# Any-authenticated-user endpoints (get_current_user) — used to prove the
# *unauthenticated* half of the matrix without asserting a specific role.
AUTHENTICATED_ONLY_GET_ENDPOINTS = [
    "/weather/forecast?lat=11.0&lon=76.9",
]


class TestUnauthenticatedAccessIsRejected:
    @pytest.mark.parametrize("path", OFFICER_ONLY_GET_ENDPOINTS + FARMER_ONLY_GET_ENDPOINTS)
    def test_protected_endpoint_requires_auth_header(self, api, api_url, path):
        """
        CATEGORY: Authorization
        TITLE: Protected endpoint rejects requests with no Authorization header
        TEST_DATA: path={path}
        EXPECTED: 401 Unauthorized or 403 Forbidden (FastAPI HTTPBearer default), never 200
        SEVERITY: High
        """
        r = api.get(api_url(path))
        assert r.status_code in (401, 403), f"{path} -> {r.status_code}: {r.text}"

    def test_farm_create_requires_auth(self, api, api_url):
        """
        CATEGORY: Authorization
        TITLE: Farm creation rejects unauthenticated requests
        EXPECTED: 401/403
        SEVERITY: High
        """
        r = api.post(api_url("/farms/"), json={"name": "x", "area_acres": 1, "latitude": 1, "longitude": 1, "district": "x"})
        assert r.status_code in (401, 403)

    def test_ai_chat_requires_auth(self, api, api_url):
        """
        CATEGORY: Authorization
        TITLE: AI chat endpoint rejects unauthenticated requests
        EXPECTED: 401/403
        SEVERITY: High
        """
        r = api.post(api_url("/ai/chat"), json={"message": "hello"})
        assert r.status_code in (401, 403)


class TestOfficerOnlyEndpointsRejectFarmer:
    @pytest.mark.parametrize("path", OFFICER_ONLY_GET_ENDPOINTS)
    def test_farmer_cannot_access_officer_dashboard(self, api, api_url, farmer1_headers, path):
        """
        CATEGORY: Authorization
        TITLE: Officer-only dashboard endpoint rejects a farmer-role token
        TEST_DATA: path={path}, role=farmer
        EXPECTED: 403 Forbidden
        SEVERITY: Critical
        """
        r = api.get(api_url(path), headers=farmer1_headers)
        assert r.status_code == 403, f"{path} -> {r.status_code}: {r.text}"

    def test_farmer_cannot_access_pest_spread_risk(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Authorization
        TITLE: Officer-only pest-spread-risk endpoint rejects a farmer-role token
        EXPECTED: 403 Forbidden
        SEVERITY: Critical
        """
        r = api.get(api_url("/dashboard/pest-spread-risk?district=Coimbatore"), headers=farmer1_headers)
        assert r.status_code == 403


class TestFarmerOnlyEndpointsRejectOfficer:
    @pytest.mark.parametrize("path", FARMER_ONLY_GET_ENDPOINTS)
    def test_officer_cannot_access_farmer_only_route(self, api, api_url, officer_headers, path):
        """
        CATEGORY: Authorization
        TITLE: Farmer-only endpoint rejects an officer-role token
        TEST_DATA: path={path}, role=officer
        EXPECTED: 403 Forbidden
        SEVERITY: High
        """
        r = api.get(api_url(path), headers=officer_headers)
        assert r.status_code == 403, f"{path} -> {r.status_code}: {r.text}"

    def test_officer_cannot_create_farm(self, api, api_url, officer_headers):
        """
        CATEGORY: Authorization
        TITLE: Officer role cannot create a farm (farmer-only action)
        EXPECTED: 403 Forbidden
        SEVERITY: High
        """
        r = api.post(
            api_url("/farms/"),
            json={"name": "x", "area_acres": 1, "latitude": 1, "longitude": 1, "district": "x"},
            headers=officer_headers,
        )
        assert r.status_code == 403

    def test_officer_cannot_use_ai_chat(self, api, api_url, officer_headers):
        """
        CATEGORY: Authorization
        TITLE: Officer role cannot call the farmer AI chat endpoint
        EXPECTED: 403 Forbidden
        SEVERITY: Medium
        """
        r = api.post(api_url("/ai/chat"), json={"message": "hi"}, headers=officer_headers)
        assert r.status_code == 403

    def test_officer_cannot_detect_disease(self, api, api_url, officer_headers):
        """
        CATEGORY: Authorization
        TITLE: Officer role cannot call the farmer-only disease detection endpoint
        EXPECTED: 403 Forbidden
        SEVERITY: Medium
        """
        r = api.post(
            api_url("/disease/detect"),
            data={"farm_id": "00000000-0000-0000-0000-000000000000"},
            files={"image": ("x.jpg", b"not-really-an-image", "image/jpeg")},
            headers=officer_headers,
        )
        assert r.status_code == 403


class TestAdminBoundary:
    def test_admin_can_access_officer_dashboard(self, api, api_url, admin_headers):
        """
        CATEGORY: Authorization
        TITLE: Admin role is accepted by officer-tier endpoints (require_officer allows admin)
        EXPECTED: 200 OK
        SEVERITY: Low
        """
        r = api.get(api_url("/dashboard/overview"), headers=admin_headers)
        assert r.status_code == 200

    def test_admin_cannot_use_farmer_only_endpoint(self, api, api_url, admin_headers):
        """
        CATEGORY: Authorization
        TITLE: Admin role is rejected by strictly farmer-only endpoints
        EXPECTED: 403 Forbidden
        SEVERITY: Medium
        """
        r = api.get(api_url("/farmers/me"), headers=admin_headers)
        assert r.status_code == 403


class TestMalformedAuthHeader:
    @pytest.mark.parametrize(
        "header_value",
        [
            "Bearer",  # missing token
            "Token abc123",  # wrong scheme
            "Bearer ",  # empty token
            "abc123",  # no scheme at all
        ],
    )
    def test_malformed_authorization_header_rejected(self, api, api_url, header_value):
        """
        CATEGORY: Authorization
        TITLE: Malformed Authorization header is rejected, not silently ignored
        TEST_DATA: Authorization={header_value}
        EXPECTED: 401 or 403, never 200
        SEVERITY: Medium
        """
        r = api.get(api_url("/farms/"), headers={"Authorization": header_value})
        assert r.status_code in (401, 403), r.text
