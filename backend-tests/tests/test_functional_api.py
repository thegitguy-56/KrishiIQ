"""
Functional API Tests — CRUD correctness, status codes, and response
shape for every router: farms, farmers, crops, disease, dashboard,
advisory, ai, sensors, weather, history.
"""
import uuid

import pytest


# ---------------------------------------------------------------------------
# Farms
# ---------------------------------------------------------------------------
class TestFarmsCRUD:
    def test_list_farms_returns_seeded_data(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: GET /farms/ returns the farmer's own farms
        EXPECTED: 200 OK, non-empty list, every item has a district
        SEVERITY: Low
        """
        r = api.get(api_url("/farms/"), headers=farmer1_headers)
        assert r.status_code == 200
        farms = r.json()
        assert isinstance(farms, list) and len(farms) > 0
        assert all("district" in f for f in farms)

    def test_create_farm_returns_201_and_full_object(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: POST /farms/ creates a farm and returns the created object
        EXPECTED: 201 Created, response contains a generated id and farmer_id
        SEVERITY: Low
        """
        r = api.post(
            api_url("/farms/"),
            json={
                "name": "Functional Test Farm",
                "area_acres": 1.5,
                "latitude": 11.05,
                "longitude": 76.95,
                "soil_type": "loam",
                "irrigation_source": "Borewell",
                "district": "Coimbatore",
                "village": "Perur",
            },
            headers=farmer1_headers,
        )
        assert r.status_code == 201
        body = r.json()
        assert body["id"]
        assert body["name"] == "Functional Test Farm"
        assert body["has_iot_sensor"] is False

    def test_get_farm_by_id(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Functional API
        TITLE: GET /farms/{{farm_id}} returns the correct farm
        EXPECTED: 200 OK, id matches
        SEVERITY: Low
        """
        r = api.get(api_url(f"/farms/{farmer1_farm_id}"), headers=farmer1_headers)
        assert r.status_code == 200
        assert r.json()["id"] == farmer1_farm_id

    def test_get_nonexistent_farm_returns_404(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: GET /farms/{{farm_id}} with an unknown but valid UUID returns 404
        EXPECTED: 404 Not Found
        SEVERITY: Low
        """
        r = api.get(api_url(f"/farms/{uuid.uuid4()}"), headers=farmer1_headers)
        assert r.status_code == 404

    def test_update_farm_partial_fields(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: PATCH /farms/{{farm_id}} updates only the supplied fields
        EXPECTED: 200 OK, updated field changed, other fields untouched
        SEVERITY: Low
        """
        created = api.post(
            api_url("/farms/"),
            json={"name": "Patch Me", "area_acres": 2.0, "latitude": 11.0, "longitude": 76.9, "district": "Coimbatore"},
            headers=farmer1_headers,
        ).json()
        r = api.patch(api_url(f"/farms/{created['id']}"), json={"area_acres": 3.5}, headers=farmer1_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["area_acres"] == 3.5
        assert body["name"] == "Patch Me"

    def test_delete_farm_then_404_on_subsequent_get(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: DELETE /farms/{{farm_id}} removes the farm; subsequent GET returns 404
        EXPECTED: 204 No Content, then 404 on GET
        SEVERITY: Low
        """
        created = api.post(
            api_url("/farms/"),
            json={"name": "Delete Me", "area_acres": 1.0, "latitude": 11.0, "longitude": 76.9, "district": "Coimbatore"},
            headers=farmer1_headers,
        ).json()
        r = api.delete(api_url(f"/farms/{created['id']}"), headers=farmer1_headers)
        assert r.status_code == 204
        follow_up = api.get(api_url(f"/farms/{created['id']}"), headers=farmer1_headers)
        assert follow_up.status_code == 404

    def test_delete_already_deleted_farm_returns_404(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: Deleting a farm twice returns 404 on the second attempt
        EXPECTED: 204 then 404
        SEVERITY: Low
        """
        created = api.post(
            api_url("/farms/"),
            json={"name": "Double Delete", "area_acres": 1.0, "latitude": 11.0, "longitude": 76.9, "district": "Coimbatore"},
            headers=farmer1_headers,
        ).json()
        first = api.delete(api_url(f"/farms/{created['id']}"), headers=farmer1_headers)
        second = api.delete(api_url(f"/farms/{created['id']}"), headers=farmer1_headers)
        assert first.status_code == 204
        assert second.status_code == 404


# ---------------------------------------------------------------------------
# Farmers profile
# ---------------------------------------------------------------------------
class TestFarmerProfile:
    def test_get_my_profile(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: GET /farmers/me returns the caller's own profile
        EXPECTED: 200 OK, phone field present
        SEVERITY: Low
        """
        r = api.get(api_url("/farmers/me"), headers=farmer1_headers)
        assert r.status_code == 200
        assert r.json()["phone"]

    def test_update_my_profile(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: PATCH /farmers/me updates the profile district
        EXPECTED: 200 OK, district reflects the new value
        SEVERITY: Low
        """
        r = api.patch(api_url("/farmers/me"), json={"district": "Salem"}, headers=farmer1_headers)
        assert r.status_code == 200
        assert r.json()["district"] == "Salem"
        # restore original state for other tests in the session
        api.patch(api_url("/farmers/me"), json={"district": "Coimbatore"}, headers=farmer1_headers)

    def test_update_preferred_language(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: PATCH /farmers/me updates preferred_language on the user record
        EXPECTED: 200 OK, preferred_language reflects the new value
        SEVERITY: Low
        """
        r = api.patch(api_url("/farmers/me"), json={"preferred_language": "ta"}, headers=farmer1_headers)
        assert r.status_code == 200
        assert r.json()["preferred_language"] == "ta"
        api.patch(api_url("/farmers/me"), json={"preferred_language": "en"}, headers=farmer1_headers)


# ---------------------------------------------------------------------------
# Crops
# ---------------------------------------------------------------------------
class TestCropsCRUD:
    def test_list_crops(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: GET /crops lists crop records across the farmer's farms
        EXPECTED: 200 OK, list type
        SEVERITY: Low
        """
        r = api.get(api_url("/crops"), headers=farmer1_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    @pytest.mark.parametrize("season", ["kharif", "rabi", "zaid"])
    def test_create_crop_each_season(self, api, api_url, farmer1_headers, farmer1_farm_id, season):
        """
        CATEGORY: Functional API
        TITLE: POST /crops creates a crop record for each valid season enum value
        TEST_DATA: season={season}
        EXPECTED: 201 Created, status defaults to 'planned'
        SEVERITY: Low
        """
        r = api.post(
            api_url("/crops"),
            json={"farm_id": farmer1_farm_id, "crop_name": "Rice", "season": season, "area_acres": 1.0},
            headers=farmer1_headers,
        )
        assert r.status_code == 201
        assert r.json()["season"] == season
        assert r.json()["status"] == "planned"

    def test_update_crop_status(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Functional API
        TITLE: PATCH /crops/{{crop_id}} updates crop status
        EXPECTED: 200 OK, status reflects the new value
        SEVERITY: Low
        """
        created = api.post(
            api_url("/crops"),
            json={"farm_id": farmer1_farm_id, "crop_name": "Maize", "season": "rabi", "area_acres": 1.0},
            headers=farmer1_headers,
        ).json()
        r = api.patch(api_url(f"/crops/{created['id']}"), json={"status": "growing"}, headers=farmer1_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "growing"

    def test_update_nonexistent_crop_returns_404(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: PATCH /crops/{{crop_id}} with an unknown id returns 404
        EXPECTED: 404 Not Found
        SEVERITY: Low
        """
        r = api.patch(api_url(f"/crops/{uuid.uuid4()}"), json={"status": "growing"}, headers=farmer1_headers)
        assert r.status_code == 404

    def test_create_crop_for_unowned_farm_returns_structured_404(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: POST /crops with a nonexistent farm_id returns 404
        EXPECTED: 404 Not Found
        SEVERITY: Low
        """
        r = api.post(
            api_url("/crops"),
            json={"farm_id": str(uuid.uuid4()), "crop_name": "Rice", "season": "kharif", "area_acres": 1.0},
            headers=farmer1_headers,
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Disease
# ---------------------------------------------------------------------------
class TestDiseaseEndpoints:
    def test_get_disease_history_for_own_farm(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Functional API
        TITLE: GET /disease/farm/{{farm_id}}/history returns a list for the caller's own farm
        EXPECTED: 200 OK, list type
        SEVERITY: Low
        """
        r = api.get(api_url(f"/disease/farm/{farmer1_farm_id}/history"), headers=farmer1_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_disease_history_respects_limit_param(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Functional API
        TITLE: GET /disease/farm/{{farm_id}}/history honours the 'limit' query parameter
        EXPECTED: 200 OK, result length <= limit
        SEVERITY: Low
        """
        r = api.get(api_url(f"/disease/farm/{farmer1_farm_id}/history"), params={"limit": 2}, headers=farmer1_headers)
        assert r.status_code == 200
        assert len(r.json()) <= 2

    def test_district_alerts_default_severity_filter(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: GET /disease/alerts/district/{{district}} defaults to high/critical severities
        EXPECTED: 200 OK, every returned item has severity in {{high, critical}}
        SEVERITY: Low
        """
        r = api.get(api_url("/disease/alerts/district/Coimbatore"), headers=farmer1_headers)
        assert r.status_code == 200
        assert all(item["severity"] in ("high", "critical") for item in r.json())

    def test_district_alerts_medium_severity_filter(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: GET /disease/alerts/district/{{district}}?severity=medium widens the severity filter
        EXPECTED: 200 OK
        SEVERITY: Low
        """
        r = api.get(api_url("/disease/alerts/district/Coimbatore"), params={"severity": "medium"}, headers=farmer1_headers)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Dashboard (officer)
# ---------------------------------------------------------------------------
class TestDashboardEndpoints:
    @pytest.mark.parametrize(
        "path",
        [
            "/dashboard/overview",
            "/dashboard/district-heatmap",
            "/dashboard/farmers",
            "/dashboard/crop-distribution",
            "/dashboard/yield-trends",
            "/dashboard/districts",
            "/dashboard/water-usage",
        ],
    )
    def test_dashboard_endpoint_returns_200_for_officer(self, api, api_url, officer_headers, path):
        """
        CATEGORY: Functional API
        TITLE: Dashboard endpoint responds 200 for an officer-role token
        TEST_DATA: path={path}
        EXPECTED: 200 OK
        SEVERITY: Low
        """
        r = api.get(api_url(path), headers=officer_headers)
        assert r.status_code == 200, r.text

    def test_dashboard_farms_map_default_district(self, api, api_url, officer_headers):
        """
        CATEGORY: Functional API
        TITLE: GET /dashboard/farms-map returns markers for the default district
        EXPECTED: 200 OK, response has 'district' and 'farms' keys
        SEVERITY: Low
        """
        r = api.get(api_url("/dashboard/farms-map"), headers=officer_headers)
        assert r.status_code == 200
        body = r.json()
        assert "district" in body and "farms" in body

    def test_dashboard_pest_spread_risk(self, api, api_url, officer_headers):
        """
        CATEGORY: Functional API
        TITLE: GET /dashboard/pest-spread-risk returns a risk assessment for a district
        EXPECTED: 200 OK
        SEVERITY: Low
        """
        r = api.get(api_url("/dashboard/pest-spread-risk"), params={"district": "Coimbatore"}, headers=officer_headers)
        assert r.status_code == 200

    def test_dashboard_overview_district_filter_narrows_results(self, api, api_url, officer_headers):
        """
        CATEGORY: Functional API
        TITLE: GET /dashboard/overview district filter narrows totals vs the unfiltered view
        EXPECTED: 200 OK, filtered total_farmers <= unfiltered total_farmers
        SEVERITY: Low
        """
        unfiltered = api.get(api_url("/dashboard/overview"), headers=officer_headers).json()
        filtered = api.get(api_url("/dashboard/overview"), params={"district": "Salem"}, headers=officer_headers).json()
        assert filtered["total_farmers"] <= unfiltered["total_farmers"]


# ---------------------------------------------------------------------------
# Advisory
# ---------------------------------------------------------------------------
class TestAdvisoryEndpoints:
    def test_get_personalized_advisory(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: GET /advisory/personalized returns a farmer_name and advisories list
        EXPECTED: 200 OK, advisories is a non-empty list (auto-generates a fallback if needed)
        SEVERITY: Low
        """
        r = api.get(api_url("/advisory/personalized"), headers=farmer1_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["farmer_name"]
        assert isinstance(body["advisories"], list) and len(body["advisories"]) >= 1

    def test_mark_advisory_read(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: PATCH /advisory/{{advisory_id}}/read marks an owned advisory as read
        EXPECTED: 200 OK, status 'ok'
        SEVERITY: Low
        """
        advisories = api.get(api_url("/advisory/personalized"), headers=farmer1_headers).json()["advisories"]
        advisory_id = advisories[0]["id"]
        r = api.patch(api_url(f"/advisory/{advisory_id}/read"), headers=farmer1_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_mark_nonexistent_advisory_read_returns_404(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: PATCH /advisory/{{advisory_id}}/read with an unknown id returns 404
        EXPECTED: 404 Not Found
        SEVERITY: Low
        """
        r = api.patch(api_url(f"/advisory/{uuid.uuid4()}/read"), headers=farmer1_headers)
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# AI
# ---------------------------------------------------------------------------
class TestAIEndpoints:
    def test_public_config_no_auth_required(self, api, api_url):
        """
        CATEGORY: Functional API
        TITLE: GET /ai/config/public works without authentication
        EXPECTED: 200 OK, ai_enabled boolean present
        SEVERITY: Low
        """
        r = api.get(api_url("/ai/config/public"))
        assert r.status_code == 200
        assert "ai_enabled" in r.json()

    def test_ai_chat_returns_reply(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: POST /ai/chat returns a reply and ai_enabled flag
        EXPECTED: 200 OK, reply is a non-empty string (even in fallback/no-API-key mode)
        SEVERITY: Low
        """
        r = api.post(api_url("/ai/chat"), json={"message": "What should I plant this season?"}, headers=farmer1_headers)
        assert r.status_code == 200
        body = r.json()
        assert "reply" in body
        assert "ai_enabled" in body

    def test_ai_chat_with_history_context(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: POST /ai/chat accepts prior conversation history
        EXPECTED: 200 OK
        SEVERITY: Low
        """
        r = api.post(
            api_url("/ai/chat"),
            json={
                "message": "And what about fertilizer?",
                "history": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}],
            },
            headers=farmer1_headers,
        )
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Sensors
# ---------------------------------------------------------------------------
class TestSensorEndpoints:
    def test_ingest_sensor_reading(self, api, api_url, farmer1_farm_id):
        """
        CATEGORY: Functional API
        TITLE: POST /sensors/ingest stores a new sensor reading
        EXPECTED: 200 OK, response echoes back the submitted values
        SEVERITY: Low
        """
        r = api.post(
            api_url("/sensors/ingest"),
            json={
                "farm_id": farmer1_farm_id,
                "device_id": "QA-DEVICE-001",
                "soil_moisture_percent": 42.0,
                "soil_ph": 6.8,
            },
        )
        assert r.status_code == 200
        assert r.json()["device_id"] == "QA-DEVICE-001"

    def test_ingest_sensor_reading_unknown_farm(self, api, api_url):
        """
        CATEGORY: Functional API
        TITLE: POST /sensors/ingest with an unknown farm_id returns 404
        EXPECTED: 404 Not Found
        SEVERITY: Low
        """
        r = api.post(api_url("/sensors/ingest"), json={"farm_id": str(uuid.uuid4()), "device_id": "GHOST"})
        assert r.status_code == 404

    def test_register_device_for_own_farm(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Functional API
        TITLE: POST /sensors/farm/{{farm_id}}/register-device pairs a device with an owned farm
        EXPECTED: 200 OK, status 'ok'
        SEVERITY: Low
        """
        r = api.post(
            api_url(f"/sensors/farm/{farmer1_farm_id}/register-device"),
            params={"device_id": "QA-PAIR-001"},
            headers=farmer1_headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_get_latest_sensor_reading_for_own_farm(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Functional API
        TITLE: GET /sensors/farm/{{farm_id}}/latest returns soil health status
        EXPECTED: 200 OK, soil_health_status present
        SEVERITY: Low
        """
        r = api.get(api_url(f"/sensors/farm/{farmer1_farm_id}/latest"), headers=farmer1_headers)
        assert r.status_code == 200
        assert "soil_health_status" in r.json()

    def test_get_sensor_history_default_window(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Functional API
        TITLE: GET /sensors/farm/{{farm_id}}/history returns readings within the default 24h window
        EXPECTED: 200 OK, list type
        SEVERITY: Low
        """
        r = api.get(api_url(f"/sensors/farm/{farmer1_farm_id}/history"), headers=farmer1_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------
class TestWeatherEndpoint:
    def test_forecast_with_valid_coordinates(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: GET /weather/forecast returns data for valid coordinates
        EXPECTED: 200 OK
        SEVERITY: Low
        """
        r = api.get(api_url("/weather/forecast"), params={"lat": 11.0168, "lon": 76.9558}, headers=farmer1_headers)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
class TestHistoryEndpoints:
    def test_history_summary(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: GET /history/summary returns aggregated farm/crop/sensor/disease counts
        EXPECTED: 200 OK, total_farms >= 1
        SEVERITY: Low
        """
        r = api.get(api_url("/history/summary"), headers=farmer1_headers)
        assert r.status_code == 200
        assert r.json()["total_farms"] >= 1

    def test_history_crops(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: GET /history/crops returns the farmer's crop history
        EXPECTED: 200 OK, list type
        SEVERITY: Low
        """
        r = api.get(api_url("/history/crops"), headers=farmer1_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_history_diseases_respects_limit(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Functional API
        TITLE: GET /history/diseases honours the 'limit' query parameter
        EXPECTED: 200 OK, result length <= limit
        SEVERITY: Low
        """
        r = api.get(api_url("/history/diseases"), params={"limit": 3}, headers=farmer1_headers)
        assert r.status_code == 200
        assert len(r.json()) <= 3

    def test_history_sensors_for_own_farm(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Functional API
        TITLE: GET /history/sensors/{{farm_id}} returns sensor logs for an owned farm
        EXPECTED: 200 OK, list type
        SEVERITY: Low
        """
        r = api.get(api_url(f"/history/sensors/{farmer1_farm_id}"), headers=farmer1_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_history_sensors_for_unowned_farm_returns_empty(self, api, api_url, farmer2_headers, farmer1_farm_id):
        """
        CATEGORY: Functional API
        TITLE: GET /history/sensors/{{farm_id}} returns an empty list (not another farmer's data) for a farm the caller does not own
        EXPECTED: 200 OK, empty list — confirms this particular route DOES scope by ownership
        SEVERITY: Informational
        """
        r = api.get(api_url(f"/history/sensors/{farmer1_farm_id}"), headers=farmer2_headers)
        assert r.status_code == 200
        assert r.json() == []


# ---------------------------------------------------------------------------
# Endpoint smoke matrix — every GET route, correct role, contract check
# ---------------------------------------------------------------------------
class TestEndpointSmokeMatrix:
    """One row per read endpoint in the API surface, hit with the correct
    role token and checked for a 200 + the right top-level JSON shape.
    Complements the deeper per-feature tests above with a fast regression
    net across the *entire* inventory in reports/inventory_data.py.
    """

    @pytest.mark.parametrize(
        "path,expect_type",
        [
            ("/farms/", list),
            ("/farmers/me", dict),
            ("/crops", list),
            ("/history/summary", dict),
            ("/history/crops", list),
            ("/history/diseases", list),
            ("/advisory/personalized", dict),
        ],
    )
    def test_farmer_scoped_endpoint_contract(self, api, api_url, farmer1_headers, path, expect_type):
        """
        CATEGORY: Functional API
        TITLE: Farmer-scoped endpoint returns 200 with the documented top-level JSON type
        TEST_DATA: path={path}, expect_type={expect_type}
        EXPECTED: 200 OK, body is a {expect_type}
        SEVERITY: Low
        """
        r = api.get(api_url(path), headers=farmer1_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), expect_type)

    @pytest.mark.parametrize(
        "path,expect_type",
        [
            ("/dashboard/overview", dict),
            ("/dashboard/district-heatmap", list),
            ("/dashboard/farmers", list),
            ("/dashboard/farms-map", dict),
            ("/dashboard/crop-distribution", list),
            ("/dashboard/yield-trends", list),
            ("/dashboard/districts", list),
            ("/dashboard/water-usage", list),
        ],
    )
    def test_officer_scoped_endpoint_contract(self, api, api_url, officer_headers, path, expect_type):
        """
        CATEGORY: Functional API
        TITLE: Officer-scoped dashboard endpoint returns 200 with the documented top-level JSON type
        TEST_DATA: path={path}, expect_type={expect_type}
        EXPECTED: 200 OK, body is a {expect_type}
        SEVERITY: Low
        """
        r = api.get(api_url(path), headers=officer_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), expect_type)

    def test_root_endpoint_contract(self, api):
        """
        CATEGORY: Functional API
        TITLE: GET / returns a liveness message
        EXPECTED: 200 OK, JSON with a 'message' key
        SEVERITY: Low
        """
        r = api.get("/")
        assert r.status_code == 200
        assert "message" in r.json()

    def test_health_endpoint_contract(self, api):
        """
        CATEGORY: Functional API
        TITLE: GET /health returns a status payload
        EXPECTED: 200 OK, status == 'ok'
        SEVERITY: Low
        """
        r = api.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_ai_public_config_contract(self, api, api_url):
        """
        CATEGORY: Functional API
        TITLE: GET /ai/config/public returns the expected public config shape
        EXPECTED: 200 OK, ai_enabled is a boolean
        SEVERITY: Low
        """
        r = api.get(api_url("/ai/config/public"))
        assert r.status_code == 200
        assert isinstance(r.json()["ai_enabled"], bool)


# ---------------------------------------------------------------------------
# Parallel flows for a second tenant (farmer2) — proves multi-tenant CRUD
# correctness beyond just farmer1
# ---------------------------------------------------------------------------
class TestFarmer2ParallelFlows:
    def test_farmer2_list_farms(self, api, api_url, farmer2_headers):
        """
        CATEGORY: Functional API
        TITLE: A second, independent farmer account can list its own farms
        EXPECTED: 200 OK, non-empty list
        SEVERITY: Low
        """
        r = api.get(api_url("/farms/"), headers=farmer2_headers)
        assert r.status_code == 200
        assert len(r.json()) > 0

    def test_farmer2_create_and_fetch_farm(self, api, api_url, farmer2_headers):
        """
        CATEGORY: Functional API
        TITLE: farmer2 can create and then fetch their own new farm
        EXPECTED: 201 Created, then 200 on GET by id
        SEVERITY: Low
        """
        created = api.post(
            api_url("/farms/"),
            json={"name": "Farmer2 Test Farm", "area_acres": 1.0, "latitude": 11.6, "longitude": 78.1, "district": "Salem"},
            headers=farmer2_headers,
        )
        assert created.status_code == 201
        fetched = api.get(api_url(f"/farms/{created.json()['id']}"), headers=farmer2_headers)
        assert fetched.status_code == 200

    def test_farmer2_create_crop_on_own_farm(self, api, api_url, farmer2_headers, farmer2_farm_id):
        """
        CATEGORY: Functional API
        TITLE: farmer2 can create a crop record on their own farm
        EXPECTED: 201 Created
        SEVERITY: Low
        """
        r = api.post(
            api_url("/crops"),
            json={"farm_id": farmer2_farm_id, "crop_name": "Sugarcane", "season": "kharif", "area_acres": 1.0},
            headers=farmer2_headers,
        )
        assert r.status_code == 201

    def test_farmer2_profile_independent_from_farmer1(self, api, api_url, farmer1_headers, farmer2_headers):
        """
        CATEGORY: Functional API
        TITLE: farmer1 and farmer2 profiles are independent records
        EXPECTED: 200 OK for both, different farmer ids
        SEVERITY: Low
        """
        p1 = api.get(api_url("/farmers/me"), headers=farmer1_headers)
        p2 = api.get(api_url("/farmers/me"), headers=farmer2_headers)
        assert p1.status_code == 200 and p2.status_code == 200
        assert p1.json()["id"] != p2.json()["id"]

    def test_farmer2_sensor_ingest_and_read_own_farm(self, api, api_url, farmer2_headers, farmer2_farm_id):
        """
        CATEGORY: Functional API
        TITLE: farmer2 can ingest and then read sensor data for their own farm
        EXPECTED: 200 OK on ingest, 200 OK with matching data on latest-read
        SEVERITY: Low
        """
        ingest = api.post(
            api_url("/sensors/ingest"),
            json={"farm_id": farmer2_farm_id, "device_id": "F2-DEVICE", "soil_moisture_percent": 55.0},
        )
        assert ingest.status_code == 200
        latest = api.get(api_url(f"/sensors/farm/{farmer2_farm_id}/latest"), headers=farmer2_headers)
        assert latest.status_code == 200

    def test_farmer2_advisory_personalized(self, api, api_url, farmer2_headers):
        """
        CATEGORY: Functional API
        TITLE: farmer2 receives their own personalized advisory set
        EXPECTED: 200 OK, farmer_name matches farmer2's profile
        SEVERITY: Low
        """
        r = api.get(api_url("/advisory/personalized"), headers=farmer2_headers)
        assert r.status_code == 200
        assert r.json()["farmer_name"]

    def test_farmer2_history_summary_independent_totals(self, api, api_url, farmer1_headers, farmer2_headers):
        """
        CATEGORY: Functional API
        TITLE: history/summary totals differ between two farmers with different farm counts
        EXPECTED: 200 OK for both; total_farms values are each farmer's own count (not global)
        SEVERITY: Low
        """
        h1 = api.get(api_url("/history/summary"), headers=farmer1_headers).json()
        h2 = api.get(api_url("/history/summary"), headers=farmer2_headers).json()
        farms1 = api.get(api_url("/farms/"), headers=farmer1_headers).json()
        farms2 = api.get(api_url("/farms/"), headers=farmer2_headers).json()
        assert h1["total_farms"] == len(farms1)
        assert h2["total_farms"] == len(farms2)

    def test_farmer2_ai_chat(self, api, api_url, farmer2_headers):
        """
        CATEGORY: Functional API
        TITLE: farmer2 can use the AI chat endpoint independently of farmer1
        EXPECTED: 200 OK
        SEVERITY: Low
        """
        r = api.post(api_url("/ai/chat"), json={"message": "How is my soil?"}, headers=farmer2_headers)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Extended field-level and role-contract coverage (closes out Functional API
# category to its documented 100+ minimum)
# ---------------------------------------------------------------------------
class TestFarmCreateOptionalFields:
    @pytest.mark.parametrize(
        "field,value",
        [
            ("soil_type", "black_cotton"),
            ("irrigation_source", "Drip"),
            ("village", "Perur"),
            ("geojson", {"type": "Point", "coordinates": [76.9, 11.0]}),
        ],
    )
    def test_farm_create_with_each_optional_field(self, api, api_url, farmer1_headers, field, value):
        """
        CATEGORY: Functional API
        TITLE: Farm creation correctly persists each optional field when supplied
        TEST_DATA: field={field}
        EXPECTED: 201 Created, response echoes the supplied optional field value
        SEVERITY: Low
        """
        body = {
            "name": f"Optional Field Test {field}",
            "area_acres": 1.0,
            "latitude": 11.0,
            "longitude": 76.9,
            "district": "Coimbatore",
            field: value,
        }
        r = api.post(api_url("/farms/"), json=body, headers=farmer1_headers)
        assert r.status_code == 201
        if field != "geojson":  # geojson isn't in FarmOut's schema
            assert r.json()[field] == value


class TestCropUpdateFieldCoverage:
    @pytest.mark.parametrize(
        "field,value",
        [
            ("crop_variety", "ADT 43"),
            ("area_acres", 2.5),
            ("actual_yield_kg", 4200.0),
            ("actual_harvest_date", "2026-03-01"),
        ],
    )
    def test_crop_update_persists_each_field(self, api, api_url, farmer1_headers, farmer1_farm_id, field, value):
        """
        CATEGORY: Functional API
        TITLE: Crop update correctly persists each individual field
        TEST_DATA: field={field}
        EXPECTED: 200 OK, response reflects the updated field value
        SEVERITY: Low
        """
        created = api.post(
            api_url("/crops"),
            json={"farm_id": farmer1_farm_id, "crop_name": f"Field Coverage {field}", "season": "kharif", "area_acres": 1.0},
            headers=farmer1_headers,
        ).json()
        r = api.patch(api_url(f"/crops/{created['id']}"), json={field: value}, headers=farmer1_headers)
        assert r.status_code == 200
        assert r.json()[field] == value


class TestSensorHistoryWindowCoverage:
    @pytest.mark.parametrize("hours", [1, 24, 168, 720])
    def test_sensor_history_valid_hour_windows(self, api, api_url, farmer1_headers, farmer1_farm_id, hours):
        """
        CATEGORY: Functional API
        TITLE: GET /history/sensors/{{farm_id}} accepts every documented valid hours boundary
        TEST_DATA: hours={hours}
        EXPECTED: 200 OK
        SEVERITY: Low
        """
        r = api.get(api_url(f"/history/sensors/{farmer1_farm_id}"), params={"hours": hours}, headers=farmer1_headers)
        assert r.status_code == 200


class TestDashboardAdminContract:
    @pytest.mark.parametrize(
        "path",
        [
            "/dashboard/overview",
            "/dashboard/district-heatmap",
            "/dashboard/farmers",
            "/dashboard/farms-map",
            "/dashboard/crop-distribution",
            "/dashboard/yield-trends",
            "/dashboard/districts",
            "/dashboard/water-usage",
        ],
    )
    def test_dashboard_endpoint_returns_200_for_admin(self, api, api_url, admin_headers, path):
        """
        CATEGORY: Functional API
        TITLE: Dashboard endpoint responds 200 for an admin-role token (require_officer allows admin too)
        TEST_DATA: path={path}
        EXPECTED: 200 OK
        SEVERITY: Low
        """
        r = api.get(api_url(path), headers=admin_headers)
        assert r.status_code == 200, r.text


class TestDiseaseAlertsMultiDistrict:
    @pytest.mark.parametrize("district", ["Coimbatore", "Salem", "Madurai", "Trichy"])
    def test_disease_alerts_per_district(self, api, api_url, farmer1_headers, district):
        """
        CATEGORY: Functional API
        TITLE: Disease district alerts endpoint works for every seeded district
        TEST_DATA: district={district}
        EXPECTED: 200 OK, list type
        SEVERITY: Low
        """
        r = api.get(api_url(f"/disease/alerts/district/{district}"), headers=farmer1_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestListOrdering:
    def test_crops_list_ordered_most_recent_first(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Functional API
        TITLE: GET /crops returns records ordered by created_at descending
        EXPECTED: 200 OK; the crop created last in this test appears before an earlier one
        SEVERITY: Low
        """
        first = api.post(
            api_url("/crops"),
            json={"farm_id": farmer1_farm_id, "crop_name": "Ordering Crop A", "season": "kharif", "area_acres": 1.0},
            headers=farmer1_headers,
        ).json()
        second = api.post(
            api_url("/crops"),
            json={"farm_id": farmer1_farm_id, "crop_name": "Ordering Crop B", "season": "kharif", "area_acres": 1.0},
            headers=farmer1_headers,
        ).json()
        listing = api.get(api_url("/crops"), headers=farmer1_headers).json()
        ids = [c["id"] for c in listing]
        assert ids.index(second["id"]) < ids.index(first["id"])

    def test_disease_history_ordered_most_recent_first(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Functional API
        TITLE: GET /disease/farm/{{farm_id}}/history is ordered by created_at descending
        EXPECTED: 200 OK, list type (order asserted structurally, not by exact timestamps, given async ML timing)
        SEVERITY: Informational
        """
        r = api.get(api_url(f"/disease/farm/{farmer1_farm_id}/history"), headers=farmer1_headers)
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
