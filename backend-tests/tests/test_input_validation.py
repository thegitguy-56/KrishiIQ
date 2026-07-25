"""
Input Validation Tests — type coercion, boundary values, malformed
identifiers, and oversized payloads across the write-capable endpoints.
"""
import pytest

from payloads import BOUNDARY_NUMBERS, INVALID_UUIDS


class TestFarmCreateValidation:
    VALID_FARM = {
        "name": "Validation Farm",
        "area_acres": 2.0,
        "latitude": 11.0,
        "longitude": 76.9,
        "district": "Coimbatore",
    }

    @pytest.mark.parametrize("field", ["name", "area_acres", "latitude", "longitude", "district"])
    def test_missing_required_field_rejected(self, api, api_url, farmer1_headers, field):
        """
        CATEGORY: Input Validation
        TITLE: Farm creation rejects payload missing a required field
        TEST_DATA: missing_field={field}
        EXPECTED: 422 Unprocessable Entity
        SEVERITY: Low
        """
        body = dict(self.VALID_FARM)
        del body[field]
        r = api.post(api_url("/farms/"), json=body, headers=farmer1_headers)
        assert r.status_code == 422

    @pytest.mark.parametrize("bad_value", BOUNDARY_NUMBERS)
    def test_area_acres_boundary_values(self, api, api_url, farmer1_headers, bad_value):
        """
        CATEGORY: Input Validation
        TITLE: Farm creation with boundary/negative area_acres values
        TEST_DATA: area_acres={bad_value}
        OBJECTIVE: Confirm the API does not silently accept negative or zero acreage
        EXPECTED: Either rejected (422/400) or accepted-and-flagged; must not 500
        SEVERITY: Medium
        """
        body = dict(self.VALID_FARM)
        body["area_acres"] = bad_value
        r = api.post(api_url("/farms/"), json=body, headers=farmer1_headers)
        assert r.status_code != 500, r.text
        if bad_value <= 0 and r.status_code == 201:
            from conftest import record_finding

            record_finding(
                finding_id="VAL-001",
                severity="Low",
                endpoint="POST /api/v1/farms/",
                description="Farm creation accepts zero or negative area_acres.",
                evidence=f"area_acres={bad_value} -> HTTP {r.status_code}",
                impact="Negative/zero land area corrupts downstream analytics (dashboard totals, yield-per-acre calculations).",
                remediation="Add a pydantic validator / Field(gt=0) constraint on FarmCreate.area_acres.",
                owasp="A04:2021 - Insecure Design",
                cwe="CWE-1284",
            )

    @pytest.mark.parametrize("lat", [-1000, 1000, "not-a-number", None])
    def test_latitude_type_and_range_validation(self, api, api_url, farmer1_headers, lat):
        """
        CATEGORY: Input Validation
        TITLE: Farm creation rejects out-of-range or wrong-type latitude
        TEST_DATA: latitude={lat}
        EXPECTED: 422 for wrong type; documents current behaviour for out-of-range floats
        SEVERITY: Low
        """
        body = dict(self.VALID_FARM)
        body["latitude"] = lat
        r = api.post(api_url("/farms/"), json=body, headers=farmer1_headers)
        if not isinstance(lat, (int, float)):
            assert r.status_code == 422
        else:
            assert r.status_code != 500

    def test_wrong_type_for_string_field(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Input Validation
        TITLE: Farm creation rejects a numeric value where a string is expected
        TEST_DATA: name=12345 (int instead of str)
        EXPECTED: 422 Unprocessable Entity
        SEVERITY: Low
        """
        body = dict(self.VALID_FARM)
        body["name"] = 12345
        r = api.post(api_url("/farms/"), json=body, headers=farmer1_headers)
        assert r.status_code == 422

    def test_extremely_long_name_field(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Input Validation
        TITLE: Farm creation with a 10,000 character name does not crash the server
        EXPECTED: 201 or 422, never 500
        SEVERITY: Low
        """
        body = dict(self.VALID_FARM)
        body["name"] = "A" * 10000
        r = api.post(api_url("/farms/"), json=body, headers=farmer1_headers)
        assert r.status_code != 500

    def test_null_body(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Input Validation
        TITLE: Farm creation with a JSON null body is rejected cleanly
        EXPECTED: 422, never 500
        SEVERITY: Low
        """
        r = api.post(api_url("/farms/"), content=b"null", headers={**farmer1_headers, "Content-Type": "application/json"})
        assert r.status_code == 422

    def test_array_instead_of_object(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Input Validation
        TITLE: Farm creation with a JSON array instead of an object is rejected cleanly
        EXPECTED: 422, never 500
        SEVERITY: Low
        """
        r = api.post(api_url("/farms/"), json=[1, 2, 3], headers=farmer1_headers)
        assert r.status_code == 422

    def test_extra_unknown_fields_ignored_or_rejected(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Input Validation
        TITLE: Farm creation with unexpected extra fields does not error
        EXPECTED: 201 (extras silently ignored by pydantic default config) — documents behaviour
        SEVERITY: Informational
        """
        body = dict(self.VALID_FARM)
        body["totally_unexpected_field"] = "surprise"
        r = api.post(api_url("/farms/"), json=body, headers=farmer1_headers)
        assert r.status_code in (201, 422)


class TestCropCreateValidation:
    def test_invalid_season_enum_rejected(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Input Validation
        TITLE: Crop creation rejects an invalid 'season' enum value
        TEST_DATA: season=monsoon2 (not a valid Season member)
        EXPECTED: 422 Unprocessable Entity
        SEVERITY: Low
        """
        body = {
            "farm_id": farmer1_farm_id,
            "crop_name": "Rice",
            "season": "monsoon2",
            "area_acres": 1.0,
        }
        r = api.post(api_url("/crops"), json=body, headers=farmer1_headers)
        assert r.status_code == 422

    def test_invalid_farm_id_uuid_format(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Input Validation
        TITLE: Crop creation rejects a malformed farm_id (not a UUID)
        EXPECTED: 422 Unprocessable Entity
        SEVERITY: Low
        """
        body = {"farm_id": "not-a-uuid", "crop_name": "Rice", "season": "kharif", "area_acres": 1.0}
        r = api.post(api_url("/crops"), json=body, headers=farmer1_headers)
        assert r.status_code == 422

    def test_negative_area_acres(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Input Validation
        TITLE: Crop creation with negative area_acres does not 500
        EXPECTED: 201 or 422, never 500
        SEVERITY: Low
        """
        body = {"farm_id": farmer1_farm_id, "crop_name": "Rice", "season": "kharif", "area_acres": -5.0}
        r = api.post(api_url("/crops"), json=body, headers=farmer1_headers)
        assert r.status_code != 500

    def test_invalid_date_format(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Input Validation
        TITLE: Crop creation rejects an unparsable sowing_date
        TEST_DATA: sowing_date="32/13/2026"
        EXPECTED: 422 Unprocessable Entity
        SEVERITY: Low
        """
        body = {
            "farm_id": farmer1_farm_id,
            "crop_name": "Rice",
            "season": "kharif",
            "area_acres": 1.0,
            "sowing_date": "32/13/2026",
        }
        r = api.post(api_url("/crops"), json=body, headers=farmer1_headers)
        assert r.status_code == 422


class TestPathParamValidation:
    @pytest.mark.parametrize("bad_id", INVALID_UUIDS)
    def test_get_farm_with_invalid_id_format(self, api, api_url, farmer1_headers, bad_id):
        """
        CATEGORY: Input Validation
        TITLE: GET /farms/{{farm_id}} handles malformed/invalid id path parameters safely
        TEST_DATA: farm_id={bad_id}
        EXPECTED: 404 or 422, never 200 and never 500
        SEVERITY: Medium
        """
        r = api.get(api_url(f"/farms/{bad_id}"), headers=farmer1_headers)
        assert r.status_code in (404, 422), f"{bad_id} -> {r.status_code}: {r.text}"
        assert r.status_code != 500

    @pytest.mark.parametrize("bad_id", INVALID_UUIDS)
    def test_get_sensor_latest_with_invalid_farm_id(self, api, api_url, farmer1_headers, bad_id):
        """
        CATEGORY: Input Validation
        TITLE: GET /sensors/farm/{{farm_id}}/latest handles malformed farm id safely
        TEST_DATA: farm_id={bad_id}
        EXPECTED: 404 or 422, never 500
        SEVERITY: Medium
        """
        r = api.get(api_url(f"/sensors/farm/{bad_id}/latest"), headers=farmer1_headers)
        assert r.status_code in (404, 422), f"{bad_id} -> {r.status_code}"
        assert r.status_code != 500


class TestQueryParamValidation:
    @pytest.mark.parametrize("hours", [-1, 0, "abc", 99999999])
    def test_sensor_history_hours_param_boundary(self, api, api_url, farmer1_headers, farmer1_farm_id, hours):
        """
        CATEGORY: Input Validation
        TITLE: Sensor history endpoint handles boundary/invalid 'hours' query param
        TEST_DATA: hours={hours}
        EXPECTED: 200 (bounded gracefully) or 422 for wrong type, never 500
        SEVERITY: Low
        """
        r = api.get(
            api_url(f"/sensors/farm/{farmer1_farm_id}/history"),
            params={"hours": hours},
            headers=farmer1_headers,
        )
        assert r.status_code != 500

    @pytest.mark.parametrize("hours", [-5, 0, 10000, "xyz"])
    def test_history_sensors_hours_param_is_bounded(self, api, api_url, farmer1_headers, farmer1_farm_id, hours):
        """
        CATEGORY: Input Validation
        TITLE: /history/sensors/{{farm_id}} enforces its documented hours range (1-720)
        TEST_DATA: hours={hours}
        EXPECTED: 422 for out-of-range/invalid values (ge=1, le=720 constraint)
        SEVERITY: Low
        """
        r = api.get(
            api_url(f"/history/sensors/{farmer1_farm_id}"),
            params={"hours": hours},
            headers=farmer1_headers,
        )
        if isinstance(hours, int) and 1 <= hours <= 720:
            assert r.status_code == 200
        else:
            assert r.status_code == 422

    def test_dashboard_district_query_with_special_characters(self, api, api_url, officer_headers):
        """
        CATEGORY: Input Validation
        TITLE: Dashboard district filter tolerates special characters without erroring
        TEST_DATA: district="Coimbatore'; --"
        EXPECTED: 200 with empty/filtered results, never 500
        SEVERITY: Medium
        """
        r = api.get(api_url("/dashboard/overview"), params={"district": "Coimbatore'; --"}, headers=officer_headers)
        assert r.status_code == 200

    def test_weather_forecast_missing_required_query_params(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Input Validation
        TITLE: Weather forecast endpoint requires lat and lon
        EXPECTED: 422 Unprocessable Entity
        SEVERITY: Low
        """
        r = api.get(api_url("/weather/forecast"), headers=farmer1_headers)
        assert r.status_code == 422

    @pytest.mark.parametrize("lat,lon", [("abc", "def"), (999, 999), (-999, -999)])
    def test_weather_forecast_invalid_coordinates(self, api, api_url, farmer1_headers, lat, lon):
        """
        CATEGORY: Input Validation
        TITLE: Weather forecast endpoint handles invalid/out-of-range coordinates safely
        TEST_DATA: lat={lat}, lon={lon}
        EXPECTED: 422 for wrong type; never 500 for out-of-range numeric values
        SEVERITY: Low
        """
        r = api.get(api_url("/weather/forecast"), params={"lat": lat, "lon": lon}, headers=farmer1_headers)
        if isinstance(lat, str):
            assert r.status_code == 422
        else:
            assert r.status_code != 500


class TestDiseaseUploadValidation:
    def test_non_image_file_rejected(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Input Validation
        TITLE: Disease detection rejects a non-image file upload
        EXPECTED: 400 Bad Request
        SEVERITY: Medium
        """
        r = api.post(
            api_url("/disease/detect"),
            data={"farm_id": farmer1_farm_id},
            files={"image": ("payload.txt", b"this is not an image", "text/plain")},
            headers=farmer1_headers,
        )
        assert r.status_code == 400

    def test_missing_image_field(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Input Validation
        TITLE: Disease detection rejects a request with no image file attached
        EXPECTED: 422 Unprocessable Entity
        SEVERITY: Low
        """
        r = api.post(api_url("/disease/detect"), data={"farm_id": farmer1_farm_id}, headers=farmer1_headers)
        assert r.status_code == 422

    def test_missing_farm_id_field(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Input Validation
        TITLE: Disease detection rejects a request with no farm_id form field
        EXPECTED: 422 Unprocessable Entity
        SEVERITY: Low
        """
        r = api.post(
            api_url("/disease/detect"),
            files={"image": ("x.jpg", b"\xff\xd8\xff\xe0fake", "image/jpeg")},
            headers=farmer1_headers,
        )
        assert r.status_code == 422


class TestAiChatValidation:
    def test_message_over_max_length_rejected(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Input Validation
        TITLE: AI chat rejects a message over the 2000 character limit
        EXPECTED: 422 Unprocessable Entity (pydantic Field max_length=2000)
        SEVERITY: Low
        """
        r = api.post(api_url("/ai/chat"), json={"message": "x" * 2001}, headers=farmer1_headers)
        assert r.status_code == 422

    def test_empty_message_rejected(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Input Validation
        TITLE: AI chat rejects an empty message
        EXPECTED: 422 Unprocessable Entity (pydantic Field min_length=1)
        SEVERITY: Low
        """
        r = api.post(api_url("/ai/chat"), json={"message": ""}, headers=farmer1_headers)
        assert r.status_code == 422

    def test_malformed_history_array(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Input Validation
        TITLE: AI chat rejects a malformed 'history' array (wrong item shape)
        EXPECTED: 422 Unprocessable Entity
        SEVERITY: Low
        """
        r = api.post(
            api_url("/ai/chat"),
            json={"message": "hi", "history": ["not", "a", "valid", "shape"]},
            headers=farmer1_headers,
        )
        assert r.status_code == 422
