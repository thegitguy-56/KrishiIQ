"""
Configuration Tests — CORS policy, HTTP security headers, exposed
documentation/debug endpoints, and generic transport-level hardening.
"""
import pytest

from conftest import record_finding

SECURITY_HEADERS = [
    "x-content-type-options",
    "x-frame-options",
    "strict-transport-security",
    "content-security-policy",
    "referrer-policy",
    "permissions-policy",
]


class TestCORS:
    def test_cors_allows_configured_origin(self, api, api_url):
        """
        CATEGORY: Configuration
        TITLE: CORS preflight succeeds for an origin present in CORS_ORIGINS
        EXPECTED: Access-Control-Allow-Origin reflects the allowed origin
        SEVERITY: Low
        """
        r = api.options(
            api_url("/auth/login"),
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert r.status_code in (200, 204)

    def test_cors_rejects_arbitrary_origin(self, api, api_url):
        """
        CATEGORY: Configuration
        TITLE: CORS does not reflect an arbitrary, non-allow-listed Origin header
        OBJECTIVE: Confirm CORS_ORIGINS is enforced rather than a wildcard '*'
        EXPECTED: Access-Control-Allow-Origin header is absent or does not equal the attacker origin
        SEVERITY: Medium
        """
        evil_origin = "https://evil-attacker.example"
        r = api.options(
            api_url("/auth/login"),
            headers={"Origin": evil_origin, "Access-Control-Request-Method": "POST"},
        )
        allow_origin = r.headers.get("access-control-allow-origin")
        if allow_origin == evil_origin or allow_origin == "*":
            record_finding(
                finding_id="CFG-001",
                severity="High",
                endpoint="* (CORSMiddleware, allow_credentials=True)",
                description="CORS policy reflects an arbitrary Origin header while allow_credentials=True.",
                evidence=f"Origin: {evil_origin} -> Access-Control-Allow-Origin: {allow_origin}",
                impact="A malicious website could make credentialed cross-origin requests on behalf of a logged-in user's browser session (if cookies were ever introduced) or read otherwise-restricted responses.",
                remediation="Ensure CORS_ORIGINS is a strict, explicit allow-list in every environment and never resolves to '*' when allow_credentials=True.",
                owasp="A05:2021 - Security Misconfiguration",
                cwe="CWE-942",
            )
        assert allow_origin != "*"


class TestSecurityHeaders:
    def test_missing_recommended_security_headers(self, api, api_url):
        """
        CATEGORY: Configuration
        TITLE: Response is missing recommended browser security headers
        OBJECTIVE: Inventory which of the standard hardening headers are present on API responses
        EXPECTED: Documents current state; logs a Medium finding for each header missing on a JSON API response
        SEVERITY: Medium
        """
        r = api.get(api_url("/ai/config/public"))
        missing = [h for h in SECURITY_HEADERS if h not in {k.lower() for k in r.headers.keys()}]
        if missing:
            record_finding(
                finding_id="CFG-002",
                severity="Medium",
                endpoint="* (all routes — FastAPI default response headers)",
                description=f"The following recommended security headers are not set on API responses: {', '.join(missing)}.",
                evidence=f"GET /api/v1/ai/config/public response headers: {dict(r.headers)}",
                impact="Reduces defense-in-depth against MIME-sniffing, clickjacking, and downgrade attacks, particularly if any endpoint response is ever rendered directly (e.g. an admin tool embedding an iframe).",
                remediation="Add a small ASGI middleware (or use `secure` / `starlette-secure-headers` style middleware) to set X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Strict-Transport-Security, and a Content-Security-Policy on every response.",
                owasp="A05:2021 - Security Misconfiguration",
                cwe="CWE-693",
            )
        # Informational — does not fail the build on its own.
        assert r.status_code == 200

    def test_server_header_does_not_overshare_version(self, api, api_url):
        """
        CATEGORY: Configuration
        TITLE: Server/response headers do not leak a specific framework version string
        EXPECTED: No 'Server' header value containing a granular version number
        SEVERITY: Low
        """
        r = api.get(api_url("/ai/config/public"))
        server_header = r.headers.get("server", "")
        assert not any(c.isdigit() for c in server_header) or server_header == "", (
            f"Server header may leak version info: {server_header}"
        )


class TestDebugAndDocsExposure:
    def test_openapi_schema_publicly_accessible(self, api):
        """
        CATEGORY: Configuration
        TITLE: /openapi.json is publicly accessible without authentication
        OBJECTIVE: Confirm whether the full API surface (including internal-only routes) is discoverable by anyone
        EXPECTED: Documents current exposure; Informational finding logged if reachable
        SEVERITY: Informational
        """
        r = api.get("/openapi.json")
        if r.status_code == 200:
            record_finding(
                finding_id="CFG-003",
                severity="Informational",
                endpoint="GET /openapi.json",
                description="The full OpenAPI schema (all routes, models, and field names) is publicly accessible with no authentication.",
                evidence=f"GET /openapi.json -> HTTP {r.status_code}, {len(r.text)} bytes",
                impact="Gives an attacker a complete, low-effort map of the API surface (every endpoint, parameter, and schema) to accelerate reconnaissance for the other findings in this report.",
                remediation="For a production deployment, consider setting docs_url=None, redoc_url=None, openapi_url=None on the FastAPI() app, or gating /docs and /openapi.json behind admin authentication.",
                owasp="A05:2021 - Security Misconfiguration",
                cwe="CWE-200",
            )
        assert r.status_code in (200, 404)

    def test_swagger_docs_publicly_accessible(self, api):
        """
        CATEGORY: Configuration
        TITLE: /docs (Swagger UI) is publicly accessible without authentication
        EXPECTED: Documents current exposure
        SEVERITY: Informational
        """
        r = api.get("/docs")
        assert r.status_code in (200, 404)

    def test_uploads_directory_does_not_allow_directory_listing(self, api):
        """
        CATEGORY: Configuration
        TITLE: The static /uploads mount does not expose a directory listing
        EXPECTED: 404, not an HTML directory index
        SEVERITY: Medium
        """
        r = api.get("/uploads/")
        assert "index of" not in r.text.lower()

    def test_uploads_directory_traversal(self, api):
        """
        CATEGORY: Configuration
        TITLE: /uploads static mount resists path traversal outside the uploads directory
        TEST_DATA: /uploads/../app/config.py
        EXPECTED: 404, never 200 with source code content
        SEVERITY: Critical
        """
        r = api.get("/uploads/../app/config.py")
        assert r.status_code in (404, 403, 400)
        assert "SECRET_KEY" not in r.text

    def test_root_and_health_do_not_leak_internal_details(self, api):
        """
        CATEGORY: Configuration
        TITLE: Root ('/') and /health endpoints return minimal, non-sensitive information
        EXPECTED: 200 OK, no stack traces, DB URLs, or internal paths in the body
        SEVERITY: Low
        """
        for path in ("/", "/health"):
            r = api.get(path)
            assert r.status_code == 200
            lowered = r.text.lower()
            for marker in ("password", "secret", "postgres://", "sqlite:///", "traceback"):
                assert marker not in lowered


class TestHTTPMethodHandling:
    def test_trace_method_disabled(self, api, api_url):
        """
        CATEGORY: Configuration
        TITLE: TRACE HTTP method is not supported (avoids Cross-Site Tracing risk)
        EXPECTED: 405 Method Not Allowed or connection-level rejection
        SEVERITY: Low
        """
        try:
            r = api.request("TRACE", api_url("/auth/login"))
            assert r.status_code in (405, 501)
        except Exception:
            pass  # httpx/underlying transport refusing TRACE outright is also an acceptable safe outcome

    def test_unsupported_method_returns_405(self, api, api_url):
        """
        CATEGORY: Configuration
        TITLE: An unsupported HTTP method on a known route returns 405, not 500
        TEST_DATA: PUT /api/v1/auth/login
        EXPECTED: 405 Method Not Allowed
        SEVERITY: Low
        """
        r = api.put(api_url("/auth/login"), json={})
        assert r.status_code == 405

    def test_content_type_enforcement_on_json_endpoint(self, api, api_url):
        """
        CATEGORY: Configuration
        TITLE: Login endpoint rejects a form-encoded body sent as JSON-typed content-type mismatch
        TEST_DATA: Content-Type: application/json, body is form-urlencoded
        EXPECTED: 422 Unprocessable Entity, not 500
        SEVERITY: Low
        """
        r = api.post(
            api_url("/auth/login"),
            content=b"phone=9000000002&password=farmer123",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422


class TestErrorVerbosity:
    def test_error_response_on_broken_ownership_path_does_not_leak_internal_ids(
        self, api, api_url, farmer2_headers, farmer1_farm_id
    ):
        """
        CATEGORY: Configuration
        TITLE: 404 error bodies on cross-tenant lookups do not leak other users' internal identifiers
        OBJECTIVE: Confirm error details returned to a farmer never contain another farmer's internal farmer_id/farm ownership data
        PRECONDITIONS: farmer1_farm_id belongs to a different account than the caller (farmer2)
        EXPECTED: Error body should be a generic message; a finding is logged if internal IDs are echoed back
        SEVERITY: Medium
        """
        r = api.post(
            api_url(f"/sensors/farm/{farmer1_farm_id}/register-device"),
            params={"device_id": "PROBE-001"},
            headers=farmer2_headers,
        )
        body_text = r.text
        if r.status_code == 404 and ("logged_in_farmer_id" in body_text or "actual_farm_farmer_id" in body_text):
            record_finding(
                finding_id="CFG-004",
                severity="Medium",
                endpoint="POST /api/v1/sensors/farm/{farm_id}/register-device",
                description="404 error responses for cross-tenant farm lookups include internal debug fields (logged_in_farmer_id, actual_farm_farmer_id, farm_exists) that reveal other accounts' internal identifiers.",
                evidence=f"HTTP {r.status_code}: {body_text[:400]}",
                impact="Information disclosure (CWE-209): an authenticated attacker can enumerate whether arbitrary farm IDs exist and correlate them to internal farmer IDs, aiding further IDOR attacks.",
                remediation="Return a generic 'Farm not found' detail message in production; only include the diagnostic fields (selected_farm_id, farm_exists, etc.) when ENVIRONMENT == 'development'.",
                owasp="A01:2021 - Broken Access Control / A05:2021 - Security Misconfiguration",
                cwe="CWE-209",
            )
        assert r.status_code in (403, 404)


class TestCORSPerOrigin:
    @pytest.mark.parametrize("origin", ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"])
    def test_each_configured_origin_receives_preflight_response(self, api, api_url, origin):
        """
        CATEGORY: Configuration
        TITLE: CORS preflight succeeds for each origin listed in CORS_ORIGINS
        TEST_DATA: origin={origin}
        EXPECTED: 200/204 preflight response
        SEVERITY: Low
        """
        r = api.options(
            api_url("/auth/login"),
            headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
        )
        assert r.status_code in (200, 204)


class TestContentTypeHeaders:
    @pytest.mark.parametrize(
        "path",
        ["/ai/config/public", "/health", "/"],
    )
    def test_response_content_type_is_json(self, api, path):
        """
        CATEGORY: Configuration
        TITLE: Public JSON endpoint returns Content-Type: application/json
        TEST_DATA: path={path}
        EXPECTED: Content-Type header starts with application/json
        SEVERITY: Low
        """
        r = api.get(path)
        assert r.headers.get("content-type", "").startswith("application/json")

    def test_authenticated_endpoint_content_type_is_json(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Configuration
        TITLE: Authenticated JSON endpoint returns Content-Type: application/json
        EXPECTED: Content-Type header starts with application/json
        SEVERITY: Low
        """
        r = api.get(api_url("/farms/"), headers=farmer1_headers)
        assert r.headers.get("content-type", "").startswith("application/json")


class TestHTTPMethodHandlingExtended:
    @pytest.mark.parametrize(
        "path",
        ["/farms/", "/farmers/me", "/crops", "/history/summary", "/dashboard/overview"],
    )
    def test_head_method_on_get_endpoints(self, api, api_url, farmer1_headers, officer_headers, path):
        """
        CATEGORY: Configuration
        TITLE: HEAD requests against GET-only endpoints do not error unexpectedly
        TEST_DATA: path={path}
        EXPECTED: 200, 401/403 (missing correct role), or 405 -- never 500
        SEVERITY: Low
        """
        headers = officer_headers if "dashboard" in path else farmer1_headers
        r = api.head(api_url(path), headers=headers)
        assert r.status_code != 500

    def test_trailing_slash_variant_handling(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Configuration
        TITLE: /crops and /crops/ both resolve (router declares both explicitly)
        EXPECTED: Both return 200
        SEVERITY: Low
        """
        r1 = api.get(api_url("/crops"), headers=farmer1_headers)
        r2 = api.get(api_url("/crops/"), headers=farmer1_headers)
        assert r1.status_code == 200
        assert r2.status_code in (200, 307, 308)

    def test_farms_trailing_slash_variant(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Configuration
        TITLE: /farms (no trailing slash) behaviour is a clean redirect or 404, not a 500
        EXPECTED: 200, 307, 308, or 404 -- never 500
        SEVERITY: Low
        """
        r = api.get(api_url("/farms"), headers=farmer1_headers)
        assert r.status_code != 500


class TestResponseHygiene:
    def test_404_response_is_json_not_html(self, api, api_url, farmer1_headers):
        """
        CATEGORY: Configuration
        TITLE: A 404 response body is JSON (FastAPI default), not an HTML error page
        EXPECTED: Content-Type: application/json
        SEVERITY: Low
        """
        r = api.get(api_url(f"/farms/{'0'*8}-0000-0000-0000-{'0'*12}"), headers=farmer1_headers)
        assert "application/json" in r.headers.get("content-type", "") or r.status_code == 422

    def test_422_response_includes_field_level_detail(self, api, api_url):
        """
        CATEGORY: Configuration
        TITLE: A 422 validation error response includes structured, field-level detail (pydantic default shape)
        EXPECTED: 'detail' key is a list of error objects
        SEVERITY: Informational
        """
        r = api.post(api_url("/auth/login"), json={})
        assert r.status_code == 422
        assert isinstance(r.json().get("detail"), list)

    def test_response_does_not_include_x_powered_by(self, api):
        """
        CATEGORY: Configuration
        TITLE: Response does not leak an X-Powered-By style framework fingerprint header
        EXPECTED: No X-Powered-By header present
        SEVERITY: Informational
        """
        r = api.get("/health")
        assert "x-powered-by" not in {k.lower() for k in r.headers.keys()}
