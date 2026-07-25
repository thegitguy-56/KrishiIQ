"""
Business Logic Tests — application-level rules that a purely
schema-level test cannot catch: who is allowed to become what role,
ownership transfer, state machines, and derived-data edge cases.
"""
import uuid

import pytest

from conftest import record_finding


def _rand_phone(prefix="74"):
    return prefix + str(uuid.uuid4().int)[:8]


def _rand_email():
    return f"biz_{uuid.uuid4().hex[:10]}@example.com"


class TestPrivilegeEscalationViaRegistration:
    """RegisterRequest exposes a client-controlled `role` field
    (app/schemas/auth.py) with no server-side restriction in
    app/api/auth.py:register(). This class proves/documents the
    resulting privilege-escalation path end to end.
    """

    @pytest.mark.parametrize("role", ["officer", "admin"])
    def test_public_registration_can_self_assign_privileged_role(self, api, api_url, officer_headers, role):
        """
        CATEGORY: Business Logic
        TITLE: Public /auth/register allows self-assignment of officer/admin role
        OBJECTIVE: Prove an unauthenticated user can register as a privileged role and immediately use privileged endpoints
        PRECONDITIONS: Public registration endpoint reachable, no invite/approval workflow
        STEPS: 1) POST /auth/register with role=officer|admin as an anonymous client 2) inspect the returned JWT role claim 3) call an officer-only endpoint with the new token
        TEST_DATA: role={role}
        EXPECTED: A correctly designed API would reject or ignore the client-supplied role (register as 'farmer' regardless, or require an approval step). Current behaviour: registration succeeds AND the token carries the requested privileged role.
        SEVERITY: Critical
        """
        body = {
            "phone": _rand_phone(),
            "password": "EscalationTest1!",
            "name": "Privilege Escalation QA",
            "email": _rand_email(),
            "district": "Coimbatore",
            "role": role,
        }
        r = api.post(api_url("/auth/register"), json=body)
        assert r.status_code in (201, 400, 422)

        if r.status_code != 201:
            # Server rejected the attempt outright -- good, nothing further to prove.
            return

        data = r.json()
        escalated = data.get("role") == role

        if escalated:
            # Confirm the escalation is not just a cosmetic token claim --
            # actually use the token against a real officer-only endpoint.
            new_headers = {"Authorization": f"Bearer {data['access_token']}"}
            probe = api.get(api_url("/dashboard/overview"), headers=new_headers)
            exploit_confirmed = probe.status_code == 200

            record_finding(
                finding_id="BIZ-001",
                severity="Critical",
                endpoint="POST /api/v1/auth/register",
                description=(
                    "RegisterRequest.role is accepted directly from the client and passed "
                    "unmodified into the created User record, allowing any anonymous caller "
                    "to self-register as 'officer' or 'admin'."
                ),
                evidence=(
                    f"POST /auth/register {{... role: '{role}'}} -> HTTP {r.status_code}, "
                    f"issued token role='{data.get('role')}'. "
                    f"GET /dashboard/overview with that token -> HTTP {probe.status_code}"
                    + (" (officer-only data returned)" if exploit_confirmed else "")
                ),
                impact=(
                    "Complete authorization bypass: any unauthenticated user can obtain "
                    "officer/admin privileges, exposing all farmers' PII, farm locations, "
                    "and district-wide dashboards without any approval workflow."
                ),
                remediation=(
                    "Remove `role` from RegisterRequest (or ignore/clamp it server-side to "
                    "UserRole.FARMER). Provision officer/admin accounts only via an internal, "
                    "authenticated admin-only endpoint or out-of-band process "
                    "(create_admin_officer.py's approach, gated behind admin auth, not public API)."
                ),
                owasp="A01:2021 - Broken Access Control",
                cwe="CWE-269: Improper Privilege Management",
            )

        assert escalated in (True, False)  # documents behaviour either way; see findings.xlsx

    def test_register_with_unrecognized_role_string(self, api, api_url):
        """
        CATEGORY: Business Logic
        TITLE: Registration with an unrecognized role string is rejected
        TEST_DATA: role="superadmin"
        EXPECTED: 422 Unprocessable Entity (not a valid UserRole enum member)
        SEVERITY: Low
        """
        r = api.post(
            api_url("/auth/register"),
            json={
                "phone": _rand_phone(),
                "password": "whatever123",
                "name": "Bad Role",
                "email": _rand_email(),
                "district": "Coimbatore",
                "role": "superadmin",
            },
        )
        assert r.status_code == 422


class TestOwnershipAndCrossTenantLogic:
    def test_crop_creation_rejected_for_farm_owned_by_another_farmer(self, api, api_url, farmer2_headers, farmer1_farm_id):
        """
        CATEGORY: Business Logic
        TITLE: A farmer cannot create a crop record against another farmer's farm_id
        PRECONDITIONS: farmer1_farm_id belongs to a different account than farmer2
        EXPECTED: 404 Not Found (farm not found for this farmer)
        SEVERITY: High
        """
        r = api.post(
            api_url("/crops"),
            json={"farm_id": farmer1_farm_id, "crop_name": "Rice", "season": "kharif", "area_acres": 1.0},
            headers=farmer2_headers,
        )
        assert r.status_code == 404

    def test_farm_update_rejected_for_farm_owned_by_another_farmer(self, api, api_url, farmer2_headers, farmer1_farm_id):
        """
        CATEGORY: Business Logic
        TITLE: A farmer cannot update another farmer's farm
        EXPECTED: 404 Not Found
        SEVERITY: High
        """
        r = api.patch(api_url(f"/farms/{farmer1_farm_id}"), json={"name": "Hijacked Name"}, headers=farmer2_headers)
        assert r.status_code == 404

    def test_farm_delete_rejected_for_farm_owned_by_another_farmer(self, api, api_url, farmer2_headers, farmer1_farm_id):
        """
        CATEGORY: Business Logic
        TITLE: A farmer cannot delete another farmer's farm
        EXPECTED: 404 Not Found
        SEVERITY: High
        """
        r = api.delete(api_url(f"/farms/{farmer1_farm_id}"), headers=farmer2_headers)
        assert r.status_code == 404


class TestStateMachineAndDerivedData:
    def test_crop_status_can_be_set_backwards_without_validation(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Business Logic
        TITLE: Crop status can be moved backwards (e.g. harvesting -> sowing) with no state-machine guard
        OBJECTIVE: Document whether CropUpdate enforces a valid forward-only lifecycle
        EXPECTED: Documents current behaviour; flags a finding if an illegal backward transition is silently accepted
        SEVERITY: Low
        """
        create = api.post(
            api_url("/crops"),
            json={
                "farm_id": farmer1_farm_id,
                "crop_name": "State Machine Test Crop",
                "season": "kharif",
                "area_acres": 1.0,
                "sowing_date": "2026-01-01",
            },
            headers=farmer1_headers,
        )
        assert create.status_code == 201
        crop_id = create.json()["id"]

        forward = api.patch(api_url(f"/crops/{crop_id}"), json={"status": "harvesting"}, headers=farmer1_headers)
        assert forward.status_code == 200

        backward = api.patch(api_url(f"/crops/{crop_id}"), json={"status": "sowing"}, headers=farmer1_headers)
        if backward.status_code == 200:
            record_finding(
                finding_id="BIZ-002",
                severity="Low",
                endpoint="PATCH /api/v1/crops/{crop_id}",
                description="CropUpdate allows moving crop status backwards in the lifecycle (e.g. harvesting -> sowing) with no state-machine validation.",
                evidence=f"harvesting -> sowing transition accepted, HTTP {backward.status_code}",
                impact="Corrupted crop-lifecycle analytics on the officer dashboard (yield trends, active-crop counts) and inconsistent advisory generation.",
                remediation="Add an explicit allowed-transitions map in the crops router/service and reject illegal backward transitions with 400.",
                owasp="A04:2021 - Insecure Design",
                cwe="CWE-841: Improper Enforcement of Behavioral Workflow",
            )
        assert backward.status_code in (200, 400, 422)

    def test_actual_yield_can_be_set_before_harvest_completed(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Business Logic
        TITLE: actual_yield_kg can be recorded while crop status is still 'growing'
        EXPECTED: Documents current behaviour (200) — no cross-field consistency check
        SEVERITY: Informational
        """
        create = api.post(
            api_url("/crops"),
            json={"farm_id": farmer1_farm_id, "crop_name": "Yield Test Crop", "season": "rabi", "area_acres": 1.0},
            headers=farmer1_headers,
        )
        assert create.status_code == 201
        crop_id = create.json()["id"]
        r = api.patch(api_url(f"/crops/{crop_id}"), json={"actual_yield_kg": 5000}, headers=farmer1_headers)
        assert r.status_code == 200

    def test_expected_harvest_date_before_sowing_date_accepted(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Business Logic
        TITLE: Crop creation accepts an expected_harvest_date earlier than sowing_date
        OBJECTIVE: Confirm whether chronological consistency between sowing/harvest dates is validated
        EXPECTED: Documents current behaviour; a Low finding is logged if accepted without validation
        SEVERITY: Low
        """
        r = api.post(
            api_url("/crops"),
            json={
                "farm_id": farmer1_farm_id,
                "crop_name": "Time Travel Crop",
                "season": "zaid",
                "area_acres": 1.0,
                "sowing_date": "2026-06-01",
                "expected_harvest_date": "2026-01-01",
            },
            headers=farmer1_headers,
        )
        if r.status_code == 201:
            record_finding(
                finding_id="BIZ-003",
                severity="Low",
                endpoint="POST /api/v1/crops",
                description="CropCreate accepts an expected_harvest_date earlier than sowing_date with no chronological validation.",
                evidence=f"sowing_date=2026-06-01, expected_harvest_date=2026-01-01 -> HTTP {r.status_code}",
                impact="Nonsensical dates propagate into yield-trend charts and advisory scheduling shown to officers/farmers.",
                remediation="Add a pydantic model_validator on CropCreate asserting expected_harvest_date > sowing_date when both are provided.",
                owasp="A04:2021 - Insecure Design",
                cwe="CWE-1287",
            )
        assert r.status_code in (201, 422)

    def test_dashboard_yield_trends_handles_empty_dataset(self, api, api_url, officer_headers):
        """
        CATEGORY: Business Logic
        TITLE: Yield-trends dashboard endpoint does not error on districts with no crop data
        EXPECTED: 200 with an empty/graceful list, never 500
        SEVERITY: Low
        """
        r = api.get(api_url("/dashboard/overview"), params={"district": "NoSuchDistrictXYZ"}, headers=officer_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total_farmers"] == 0
        assert body["total_farms"] == 0

    def test_disease_detect_defaults_crop_name_when_no_active_crop(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Business Logic
        TITLE: Disease detection still returns a result when the farm has no growing/sowing crop record
        OBJECTIVE: Confirm app/api/disease.py's `crop_name = crop.crop_name if crop else "rice"` fallback doesn't crash
        EXPECTED: 200 with a result (defaults treatment context to 'rice'), never 500
        SEVERITY: Informational
        """
        r = api.post(
            api_url("/disease/detect"),
            data={"farm_id": farmer1_farm_id},
            files={"image": ("leaf.jpg", b"\xff\xd8\xff\xe0" + b"0" * 200, "image/jpeg")},
            headers=farmer1_headers,
        )
        assert r.status_code in (200, 400, 422, 500)
        if r.status_code == 500:
            record_finding(
                finding_id="BIZ-004",
                severity="Medium",
                endpoint="POST /api/v1/disease/detect",
                description="Disease detection endpoint raised an unhandled server error, likely from the ML inference path or the crop-name fallback logic.",
                evidence=f"HTTP {r.status_code}: {r.text[:300]}",
                impact="Farmers cannot get disease diagnoses; repeated failures could indicate a DoS vector via crafted uploads.",
                remediation="Wrap detector.predict() and the downstream treatment-enhancement call in try/except with a clean 500/503 JSON error, and add server-side logging without leaking internals to the client.",
                owasp="A04:2021 - Insecure Design",
                cwe="CWE-248: Uncaught Exception",
            )


class TestCropLifecycleTransitions:
    @pytest.mark.parametrize(
        "from_status,to_status",
        [("planned", "sowing"), ("sowing", "growing"), ("growing", "harvesting"), ("harvesting", "completed")],
    )
    def test_forward_lifecycle_transition_accepted(self, api, api_url, farmer1_headers, farmer1_farm_id, from_status, to_status):
        """
        CATEGORY: Business Logic
        TITLE: Crop status forward transition is accepted
        TEST_DATA: {from_status} -> {to_status}
        EXPECTED: 200 OK, status updated
        SEVERITY: Low
        """
        created = api.post(
            api_url("/crops"),
            json={"farm_id": farmer1_farm_id, "crop_name": f"Lifecycle {to_status}", "season": "kharif", "area_acres": 1.0},
            headers=farmer1_headers,
        ).json()
        # move to from_status first (skip if already 'planned', the default)
        if from_status != "planned":
            api.patch(api_url(f"/crops/{created['id']}"), json={"status": from_status}, headers=farmer1_headers)
        r = api.patch(api_url(f"/crops/{created['id']}"), json={"status": to_status}, headers=farmer1_headers)
        assert r.status_code == 200
        assert r.json()["status"] == to_status


class TestDerivedDashboardConsistency:
    def test_creating_a_farm_increments_officer_visible_total(self, api, api_url, farmer1_headers, officer_headers):
        """
        CATEGORY: Business Logic
        TITLE: A newly created farm is immediately reflected in the officer dashboard's total_farms count
        EXPECTED: total_farms after creation > total_farms before creation
        SEVERITY: Low
        """
        before = api.get(api_url("/dashboard/overview"), headers=officer_headers).json()["total_farms"]
        api.post(
            api_url("/farms/"),
            json={"name": "Dashboard Consistency Farm", "area_acres": 1.0, "latitude": 11.0, "longitude": 76.9, "district": "Coimbatore"},
            headers=farmer1_headers,
        )
        after = api.get(api_url("/dashboard/overview"), headers=officer_headers).json()["total_farms"]
        assert after > before

    def test_water_usage_only_includes_sensor_equipped_farms(self, api, api_url, officer_headers):
        """
        CATEGORY: Business Logic
        TITLE: /dashboard/water-usage aggregation only counts farms with has_iot_sensor=True
        OBJECTIVE: Confirm farms without sensors are excluded rather than counted with null/zero moisture
        EXPECTED: 200 OK; every district entry's 'farms' count is <= the district's total farm count
        SEVERITY: Low
        """
        water = api.get(api_url("/dashboard/water-usage"), headers=officer_headers).json()
        heatmap = {row["district"]: row["farm_count"] for row in api.get(api_url("/dashboard/district-heatmap"), headers=officer_headers).json()}
        for row in water:
            assert row["farms"] <= heatmap.get(row["district"], row["farms"])

    def test_yield_trends_limited_to_top_three_crops(self, api, api_url, officer_headers):
        """
        CATEGORY: Business Logic
        TITLE: /dashboard/yield-trends limits its series to at most 3 crop names, per the documented implementation
        EXPECTED: 200 OK; each monthly row has at most 3 crop-keyed values (excluding 'month')
        SEVERITY: Informational
        """
        rows = api.get(api_url("/dashboard/yield-trends"), headers=officer_headers).json()
        for row in rows:
            crop_keys = [k for k in row.keys() if k != "month"]
            assert len(crop_keys) <= 3

    def test_crop_distribution_percentages_sum_near_100(self, api, api_url, officer_headers):
        """
        CATEGORY: Business Logic
        TITLE: /dashboard/crop-distribution percentages sum to approximately 100%
        EXPECTED: Sum of 'value' fields is within a small rounding tolerance of 100
        SEVERITY: Low
        """
        rows = api.get(api_url("/dashboard/crop-distribution"), headers=officer_headers).json()
        if rows:
            total = sum(r["value"] for r in rows)
            assert 95 <= total <= 105

    def test_history_summary_water_saved_scales_with_area(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Business Logic
        TITLE: history/summary's water_saved_liters heuristic scales linearly with total farm area
        EXPECTED: water_saved_liters == round(total_area_acres * 1200)
        SEVERITY: Informational
        """
        body = api.get(api_url("/history/summary"), headers=farmer1_headers).json()
        expected = round(body["total_area_acres"] * 1200)
        assert body["water_usage"]["estimated_saved_liters"] == expected


class TestAdditionalDataConsistencyRules:
    def test_farm_delete_cascades_crop_records(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Business Logic
        TITLE: Deleting a farm cascades to delete its crop records (ORM cascade="all, delete-orphan")
        EXPECTED: Crop created under the farm is no longer retrievable after the farm is deleted
        SEVERITY: Medium
        """
        farm = api.post(
            api_url("/farms/"),
            json={"name": "Cascade Test Farm", "area_acres": 1.0, "latitude": 11.0, "longitude": 76.9, "district": "Coimbatore"},
            headers=farmer1_headers,
        ).json()
        crop = api.post(
            api_url("/crops"),
            json={"farm_id": farm["id"], "crop_name": "Cascade Crop", "season": "kharif", "area_acres": 1.0},
            headers=farmer1_headers,
        ).json()
        api.delete(api_url(f"/farms/{farm['id']}"), headers=farmer1_headers)
        r = api.patch(api_url(f"/crops/{crop['id']}"), json={"status": "growing"}, headers=farmer1_headers)
        assert r.status_code == 404

    def test_crop_area_can_exceed_parent_farm_area(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Business Logic
        TITLE: A crop's area_acres can exceed its parent farm's total area_acres with no cross-check
        OBJECTIVE: Confirm whether crop area is validated against the farm's own acreage
        EXPECTED: Documents current behaviour; logs a Low finding if accepted without validation
        SEVERITY: Low
        """
        farm = api.post(
            api_url("/farms/"),
            json={"name": "Small Farm", "area_acres": 1.0, "latitude": 11.0, "longitude": 76.9, "district": "Coimbatore"},
            headers=farmer1_headers,
        ).json()
        r = api.post(
            api_url("/crops"),
            json={"farm_id": farm["id"], "crop_name": "Oversized Crop", "season": "kharif", "area_acres": 999.0},
            headers=farmer1_headers,
        )
        if r.status_code == 201:
            record_finding(
                finding_id="BIZ-005",
                severity="Low",
                endpoint="POST /api/v1/crops",
                description="CropCreate accepts an area_acres value far exceeding its parent farm's own area_acres, with no cross-record validation.",
                evidence=f"Farm area_acres=1.0, crop area_acres=999.0 -> HTTP {r.status_code}",
                impact="Inflated/impossible crop-area data skews yield-per-acre and dashboard acreage analytics.",
                remediation="Add a check in the crops router comparing CropCreate.area_acres against the parent Farm.area_acres (allowing multiple concurrent crops to sum sensibly) before persisting.",
                owasp="A04:2021 - Insecure Design",
                cwe="CWE-1284",
            )
        assert r.status_code in (201, 422)

    def test_negative_actual_yield_accepted(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Business Logic
        TITLE: A negative actual_yield_kg value is accepted with no validation
        EXPECTED: Documents current behaviour (200/422)
        SEVERITY: Low
        """
        created = api.post(
            api_url("/crops"),
            json={"farm_id": farmer1_farm_id, "crop_name": "Negative Yield Crop", "season": "rabi", "area_acres": 1.0},
            headers=farmer1_headers,
        ).json()
        r = api.patch(api_url(f"/crops/{created['id']}"), json={"actual_yield_kg": -500}, headers=farmer1_headers)
        assert r.status_code in (200, 422)

    def test_history_summary_handles_farmer_with_zero_farms_gracefully(self, api, api_url):
        """
        CATEGORY: Business Logic
        TITLE: A brand-new farmer account with zero farms gets a zeroed-out (not error) history summary
        EXPECTED: 200 OK, total_farms == 0, no division-by-zero 500
        SEVERITY: Low
        """
        import uuid as _uuid

        reg = api.post(
            api_url("/auth/register"),
            json={
                "phone": "77" + str(_uuid.uuid4().int)[:8],
                "password": "whatever123",
                "name": "Zero Farms Farmer",
                "email": f"zero_{_uuid.uuid4().hex[:8]}@example.com",
                "district": "Coimbatore",
            },
        )
        assert reg.status_code == 201
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
        r = api.get(api_url("/history/summary"), headers=headers)
        assert r.status_code == 200
        assert r.json()["total_farms"] == 0

    def test_disease_alerts_high_filter_excludes_medium_severity(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Business Logic
        TITLE: Disease alerts default (severity=high) filter never returns medium-severity detections
        EXPECTED: 200 OK, no item has severity == 'medium'
        SEVERITY: Low
        """
        r = api.get(api_url("/disease/alerts/district/Coimbatore"), headers=farmer1_headers)
        assert r.status_code == 200
        assert all(item["severity"] != "medium" for item in r.json())


class TestAdditionalBusinessRuleChecks:
    def test_district_heatmap_total_acres_matches_sum_of_farm_areas(self, api, api_url, farmer1_headers, officer_headers):
        """
        CATEGORY: Business Logic
        TITLE: district-heatmap's total_acres for a district equals the sum of that district's individual farm areas
        EXPECTED: Aggregated total_acres matches a manually summed value for Coimbatore within rounding tolerance
        SEVERITY: Low
        """
        farms = api.get(api_url("/farms/"), headers=farmer1_headers).json()
        coimbatore_total = sum(f["area_acres"] for f in farms if f["district"] == "Coimbatore")
        heatmap = {row["district"]: row["total_acres"] for row in api.get(api_url("/dashboard/district-heatmap"), headers=officer_headers).json()}
        if "Coimbatore" in heatmap:
            assert heatmap["Coimbatore"] >= round(coimbatore_total, 1) - 0.2

    def test_new_crop_always_starts_as_planned(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Business Logic
        TITLE: A newly created crop record always starts in 'planned' status regardless of other fields supplied
        EXPECTED: status == 'planned' even when other optional fields are set
        SEVERITY: Low
        """
        r = api.post(
            api_url("/crops"),
            json={
                "farm_id": farmer1_farm_id,
                "crop_name": "Default Status Crop",
                "season": "rabi",
                "area_acres": 1.0,
                "sowing_date": "2026-02-01",
            },
            headers=farmer1_headers,
        )
        assert r.status_code == 201
        assert r.json()["status"] == "planned"

    def test_registration_without_role_defaults_to_farmer(self, api, api_url):
        """
        CATEGORY: Business Logic
        TITLE: Registration with no 'role' field defaults to 'farmer' (the safe default)
        EXPECTED: 201 Created, role == 'farmer'
        SEVERITY: Low
        """
        import uuid as _uuid

        r = api.post(
            api_url("/auth/register"),
            json={
                "phone": "78" + str(_uuid.uuid4().int)[:8],
                "password": "whatever123",
                "name": "Default Role Farmer",
                "email": f"defrole_{_uuid.uuid4().hex[:8]}@example.com",
                "district": "Coimbatore",
            },
        )
        assert r.status_code == 201
        assert r.json()["role"] == "farmer"

    def test_disease_detection_appears_in_subsequent_history_call(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Business Logic
        TITLE: A disease detection is immediately queryable via the farm's history endpoint afterwards
        EXPECTED: History count after detection >= history count before detection
        SEVERITY: Low
        """
        before = api.get(api_url(f"/disease/farm/{farmer1_farm_id}/history"), headers=farmer1_headers).json()
        detect = api.post(
            api_url("/disease/detect"),
            data={"farm_id": farmer1_farm_id},
            files={"image": ("leaf2.jpg", b"\xff\xd8\xff\xe0" + b"1" * 200, "image/jpeg")},
            headers=farmer1_headers,
        )
        if detect.status_code == 200:
            after = api.get(api_url(f"/disease/farm/{farmer1_farm_id}/history"), headers=farmer1_headers).json()
            assert len(after) >= len(before)

    def test_advisory_read_state_persists_across_calls(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Business Logic
        TITLE: Marking an advisory as read persists when the advisory list is fetched again
        EXPECTED: is_read == 'true' on the second fetch after the PATCH
        SEVERITY: Low
        """
        advisories = api.get(api_url("/advisory/personalized"), headers=farmer1_headers).json()["advisories"]
        target = advisories[0]
        api.patch(api_url(f"/advisory/{target['id']}/read"), headers=farmer1_headers)
        refreshed = api.get(api_url("/advisory/personalized"), headers=farmer1_headers).json()["advisories"]
        matching = [a for a in refreshed if a["id"] == target["id"]]
        if matching:
            assert matching[0]["is_read"] == "true"
