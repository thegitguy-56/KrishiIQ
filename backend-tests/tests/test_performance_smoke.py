"""
Performance Tests (functional-level smoke checks) — response-time
budgets for individual endpoints and small concurrency bursts.

This module is intentionally lightweight: it runs inside the same
pytest session as everything else and should complete in seconds. The
authoritative load/stress testing (100 -> 1000 virtual users) is done
separately by load/k6-load-test.js and reported in performance-report.md
per the project's CI job.
"""
import concurrent.futures
import statistics
import time

import pytest

from conftest import record_finding

# Generous budgets for a cold-start ephemeral CI container running SQLite —
# tune down once you have a real performance baseline (see README.md).
LATENCY_BUDGET_MS = {
    "/health": 300,
    "/ai/config/public": 500,
    "/auth/login": 800,
    "/farms/": 800,
    "/dashboard/overview": 1200,
    "/history/summary": 1000,
}


def _timed_get(api, path, headers=None, params=None):
    start = time.perf_counter()
    r = api.get(path, headers=headers, params=params)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return r, elapsed_ms


class TestResponseTimeBudgets:
    def test_health_endpoint_latency(self, api):
        """
        CATEGORY: Performance
        TITLE: /health responds within budget
        EXPECTED: < 300ms
        SEVERITY: Low
        """
        r, ms = _timed_get(api, "/health")
        assert r.status_code == 200
        assert ms < LATENCY_BUDGET_MS["/health"], f"{ms:.0f}ms"

    def test_ai_public_config_latency(self, api, api_url):
        """
        CATEGORY: Performance
        TITLE: /ai/config/public responds within budget
        EXPECTED: < 500ms
        SEVERITY: Low
        """
        r, ms = _timed_get(api, api_url("/ai/config/public"))
        assert r.status_code == 200
        assert ms < LATENCY_BUDGET_MS["/ai/config/public"], f"{ms:.0f}ms"

    def test_login_latency(self, api, api_url):
        """
        CATEGORY: Performance
        TITLE: Login (including bcrypt password verification) responds within budget
        EXPECTED: < 800ms
        SEVERITY: Medium
        """
        start = time.perf_counter()
        r = api.post(api_url("/auth/login"), json={"phone": "9000000002", "password": "farmer123"})
        ms = (time.perf_counter() - start) * 1000
        assert r.status_code == 200
        assert ms < LATENCY_BUDGET_MS["/auth/login"], f"{ms:.0f}ms"

    def test_farms_list_latency(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Performance
        TITLE: GET /farms/ responds within budget
        EXPECTED: < 800ms
        SEVERITY: Low
        """
        r, ms = _timed_get(api, api_url("/farms/"), headers=farmer1_headers)
        assert r.status_code == 200
        assert ms < LATENCY_BUDGET_MS["/farms/"], f"{ms:.0f}ms"

    def test_dashboard_overview_latency(self, api, api_url, officer_headers):
        """
        CATEGORY: Performance
        TITLE: GET /dashboard/overview (multi-table aggregation) responds within budget
        EXPECTED: < 1200ms
        SEVERITY: Medium
        """
        r, ms = _timed_get(api, api_url("/dashboard/overview"), headers=officer_headers)
        assert r.status_code == 200
        if ms >= LATENCY_BUDGET_MS["/dashboard/overview"]:
            record_finding(
                finding_id="PERF-001",
                severity="Low",
                endpoint="GET /api/v1/dashboard/overview",
                description="Dashboard overview aggregation exceeded its latency budget under a lightly-seeded dataset.",
                evidence=f"Observed {ms:.0f}ms, budget {LATENCY_BUDGET_MS['/dashboard/overview']}ms",
                impact="Officer dashboard load times may degrade further as district/farm/crop volume grows in production.",
                remediation="Profile the overview query (it runs 3 separate COUNT/SUM queries plus a 5-row alert query); consider a single aggregated query or a materialized summary table refreshed periodically.",
                owasp="",
                cwe="CWE-1050: Excessive Platform Resource Consumption Within a Loop",
            )
        assert ms < LATENCY_BUDGET_MS["/dashboard/overview"] * 3, "Grossly exceeded even a generous 3x budget"

    def test_history_summary_latency(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Performance
        TITLE: GET /history/summary responds within budget
        EXPECTED: < 1000ms
        SEVERITY: Low
        """
        r, ms = _timed_get(api, api_url("/history/summary"), headers=farmer1_headers)
        assert r.status_code == 200
        assert ms < LATENCY_BUDGET_MS["/history/summary"], f"{ms:.0f}ms"

    @pytest.mark.parametrize(
        "path",
        [
            "/dashboard/district-heatmap",
            "/dashboard/crop-distribution",
            "/dashboard/yield-trends",
            "/dashboard/water-usage",
            "/dashboard/farms-map",
        ],
    )
    def test_secondary_dashboard_endpoints_latency(self, api, api_url, officer_headers, path):
        """
        CATEGORY: Performance
        TITLE: Secondary dashboard endpoint responds within a generous budget
        TEST_DATA: path={path}
        EXPECTED: < 2000ms
        SEVERITY: Low
        """
        r, ms = _timed_get(api, api_url(path), headers=officer_headers)
        assert r.status_code == 200
        assert ms < 2000, f"{path}: {ms:.0f}ms"


class TestConcurrencyBurst:
    @pytest.mark.parametrize("path,concurrency", [("/health", 20), ("/ai/config/public", 15)])
    def test_burst_of_concurrent_requests_all_succeed(self, api_url, path, concurrency):
        """
        CATEGORY: Performance
        TITLE: A burst of concurrent requests to a lightweight endpoint all succeed
        TEST_DATA: path={path}, concurrency={concurrency}
        EXPECTED: All requests return 200, no connection errors
        SEVERITY: Medium
        """
        import httpx

        from conftest import API_BASE_URL

        def _call():
            with httpx.Client(base_url=API_BASE_URL, timeout=10) as c:
                return c.get(path if path.startswith("/api") else path)

        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
            results = list(pool.map(lambda _: _call(), range(concurrency)))
        statuses = [r.status_code for r in results]
        assert all(s == 200 for s in statuses), statuses

    def test_burst_latency_distribution_reported(self, api, api_url):
        """
        CATEGORY: Performance
        TITLE: Latency distribution (p50/p95) for a small concurrent burst against /health is captured
        EXPECTED: p95 stays under 5x the p50 (no severe tail-latency blowup at this small scale)
        SEVERITY: Low
        """
        import httpx

        from conftest import API_BASE_URL

        def _timed():
            with httpx.Client(base_url=API_BASE_URL, timeout=10) as c:
                start = time.perf_counter()
                c.get("/health")
                return (time.perf_counter() - start) * 1000

        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as pool:
            samples = list(pool.map(lambda _: _timed(), range(25)))
        samples.sort()
        p50 = statistics.median(samples)
        p95 = samples[int(len(samples) * 0.95) - 1]
        assert p95 < max(p50 * 5, 500), f"p50={p50:.0f}ms p95={p95:.0f}ms"


class TestPaginationAndPayloadSize:
    def test_large_limit_on_history_diseases_does_not_error(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Performance
        TITLE: An unusually large 'limit' query param does not degrade into an error
        TEST_DATA: limit=100000
        EXPECTED: 200 OK, responds promptly
        SEVERITY: Low
        """
        r, ms = _timed_get(api, api_url("/history/diseases"), headers=farmer1_headers, params={"limit": 100000})
        assert r.status_code == 200
        assert ms < 3000

    def test_large_hours_window_on_sensor_history(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Performance
        TITLE: A large 'hours' window on sensor history does not degrade into an error
        TEST_DATA: hours=8760 (1 year)
        EXPECTED: 200 OK, responds promptly
        SEVERITY: Low
        """
        r, ms = _timed_get(
            api,
            api_url(f"/sensors/farm/{farmer1_farm_id}/history"),
            headers=farmer1_headers,
            params={"hours": 8760},
        )
        assert r.status_code == 200
        assert ms < 3000


class TestAdditionalEndpointLatencyBudgets:
    @pytest.mark.parametrize(
        "path,budget_ms",
        [
            ("/farmers/me", 800),
            ("/crops", 800),
            ("/history/diseases", 800),
            ("/advisory/personalized", 2000),  # generates advisories synchronously -- more expensive
        ],
    )
    def test_farmer_endpoint_latency_budget(self, api, api_url, farmer1_headers, path, budget_ms):
        """
        CATEGORY: Performance
        TITLE: Farmer-scoped endpoint responds within budget
        TEST_DATA: path={path}, budget_ms={budget_ms}
        EXPECTED: response time under budget
        SEVERITY: Low
        """
        r, ms = _timed_get(api, api_url(path), headers=farmer1_headers)
        assert r.status_code == 200
        assert ms < budget_ms, f"{path}: {ms:.0f}ms"

    def test_sensors_latest_latency(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Performance
        TITLE: GET /sensors/farm/{{farm_id}}/latest responds within budget
        EXPECTED: < 800ms
        SEVERITY: Low
        """
        r, ms = _timed_get(api, api_url(f"/sensors/farm/{farmer1_farm_id}/latest"), headers=farmer1_headers)
        assert r.status_code == 200
        assert ms < 800

    def test_weather_forecast_latency(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Performance
        TITLE: GET /weather/forecast responds within budget
        EXPECTED: < 3000ms (may hit an external weather API / cold cache)
        SEVERITY: Low
        """
        r, ms = _timed_get(api, api_url("/weather/forecast"), headers=farmer1_headers, params={"lat": 11.0, "lon": 76.9})
        assert r.status_code == 200
        assert ms < 3000


class TestConcurrencyExtended:
    def test_authenticated_burst_against_farms_list(self, api_url, farmer1_headers):
        """
        CATEGORY: Performance
        TITLE: A burst of concurrent authenticated requests against /farms/ all succeed
        EXPECTED: All 10 concurrent requests return 200
        SEVERITY: Medium
        """
        import httpx

        from conftest import API_BASE_URL

        def _call():
            with httpx.Client(base_url=API_BASE_URL, timeout=10) as c:
                return c.get("/api/v1/farms/", headers=farmer1_headers)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(lambda _: _call(), range(10)))
        assert all(r.status_code == 200 for r in results)

    def test_concurrent_logins_all_succeed(self, api_url):
        """
        CATEGORY: Performance
        TITLE: A burst of concurrent login requests for the same account all succeed
        TEST_DATA: concurrency=10
        EXPECTED: All 10 concurrent logins return 200 (bcrypt verification under concurrent load)
        SEVERITY: Medium
        """
        import httpx

        from conftest import API_BASE_URL

        def _call():
            with httpx.Client(base_url=API_BASE_URL, timeout=10) as c:
                return c.post("/api/v1/auth/login", json={"phone": "9000000002", "password": "farmer123"})

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(lambda _: _call(), range(10)))
        assert all(r.status_code == 200 for r in results)

    def test_concurrent_sensor_ingests_all_succeed(self, api_url, farmer1_farm_id):
        """
        CATEGORY: Performance
        TITLE: A burst of concurrent unauthenticated sensor ingests for the same farm all succeed
        TEST_DATA: concurrency=15
        EXPECTED: All 15 concurrent ingests return 200, no write contention errors
        SEVERITY: Medium
        """
        import httpx

        from conftest import API_BASE_URL

        def _call(i):
            with httpx.Client(base_url=API_BASE_URL, timeout=10) as c:
                return c.post(
                    "/api/v1/sensors/ingest",
                    json={"farm_id": farmer1_farm_id, "device_id": f"BURST-{i}", "soil_moisture_percent": 40.0},
                )

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as pool:
            results = list(pool.map(_call, range(15)))
        assert all(r.status_code == 200 for r in results)

    def test_officer_dashboard_moderate_concurrency(self, api_url, officer_headers):
        """
        CATEGORY: Performance
        TITLE: A moderate concurrent load (5 parallel requests) against the heaviest dashboard endpoint succeeds
        EXPECTED: All 5 concurrent requests to /dashboard/overview return 200
        SEVERITY: Low
        """
        import httpx

        from conftest import API_BASE_URL

        def _call():
            with httpx.Client(base_url=API_BASE_URL, timeout=10) as c:
                return c.get("/api/v1/dashboard/overview", headers=officer_headers)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(lambda _: _call(), range(5)))
        assert all(r.status_code == 200 for r in results)


class TestPaginationPerformanceExtended:
    def test_crop_list_latency_after_bulk_creation(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Performance
        TITLE: GET /crops stays responsive after creating a batch of crop records in this session
        OBJECTIVE: Detect an obvious N+1 query problem as the crop-record count grows
        EXPECTED: List call after 20 creations still completes under 1.5s
        SEVERITY: Low
        """
        for i in range(20):
            api.post(
                api_url("/crops"),
                json={"farm_id": farmer1_farm_id, "crop_name": f"Bulk Crop {i}", "season": "kharif", "area_acres": 0.5},
                headers=farmer1_headers,
            )
        r, ms = _timed_get(api, api_url("/crops"), headers=farmer1_headers)
        assert r.status_code == 200
        assert ms < 1500, f"{ms:.0f}ms"


class TestAdditionalLatencyBudgets:
    def test_dashboard_farmers_list_latency(self, api, api_url, officer_headers):
        """
        CATEGORY: Performance
        TITLE: GET /dashboard/farmers (per-farmer aggregation loop) responds within budget
        EXPECTED: < 2500ms even with the N+1-style per-farmer query loop in the current implementation
        SEVERITY: Medium
        """
        r, ms = _timed_get(api, api_url("/dashboard/farmers"), headers=officer_headers)
        assert r.status_code == 200
        assert ms < 2500, f"{ms:.0f}ms"

    def test_disease_history_latency(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Performance
        TITLE: GET /disease/farm/{{farm_id}}/history responds within budget
        EXPECTED: < 800ms
        SEVERITY: Low
        """
        r, ms = _timed_get(api, api_url(f"/disease/farm/{farmer1_farm_id}/history"), headers=farmer1_headers)
        assert r.status_code == 200
        assert ms < 800, f"{ms:.0f}ms"

    def test_crop_creation_write_latency(self, api, api_url, farmer1_headers, farmer1_farm_id):
        """
        CATEGORY: Performance
        TITLE: POST /crops (write path) responds within budget
        EXPECTED: < 800ms
        SEVERITY: Low
        """
        import time as _time

        start = _time.perf_counter()
        r = api.post(
            api_url("/crops"),
            json={"farm_id": farmer1_farm_id, "crop_name": "Write Latency Crop", "season": "kharif", "area_acres": 1.0},
            headers=farmer1_headers,
        )
        ms = (_time.perf_counter() - start) * 1000
        assert r.status_code == 201
        assert ms < 800, f"{ms:.0f}ms"
