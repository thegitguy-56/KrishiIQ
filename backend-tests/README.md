# KrishiIQ Backend Test Suite (Security + Load + Functional API)

Everything in this folder runs **only in GitHub Actions** — you do not
need Python, k6, or anything else installed locally. Drop it into your
repo, push, and the workflow does the rest.

## 1. Where these files go

Your repo root currently looks like:

```
KrishiIQ/
├── backend/
├── selenium-tests/
├── .github/workflows/
│   ├── deploy-frontend.yml
│   └── selenium-tests.yml
└── ...
```

Unzip this bundle so it becomes a **sibling of `backend/`**, matching the
convention your `selenium-tests/` folder already uses:

```
KrishiIQ/
├── backend/
├── backend-tests/              <-- everything in this zip's "backend-tests" folder
│   ├── pytest.ini
│   ├── requirements-test.txt
│   ├── bandit.yaml
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── payloads.py
│   │   ├── test_authentication.py
│   │   ├── test_authorization.py
│   │   ├── test_input_validation.py
│   │   ├── test_injection.py
│   │   ├── test_business_logic.py
│   │   ├── test_configuration.py
│   │   ├── test_functional_api.py
│   │   ├── test_dast.py
│   │   └── test_performance_smoke.py
│   ├── reports/
│   │   ├── inventory_data.py
│   │   └── generate_reports.py
│   └── load/
│       └── k6-load-test.js
├── selenium-tests/
└── .github/workflows/
    ├── deploy-frontend.yml
    ├── selenium-tests.yml
    └── backend-tests.yml       <-- this zip's ".github/workflows/backend-tests.yml"
```

**Concretely:**

1. Copy this zip's `backend-tests/` folder to your repo root, next to `backend/`.
2. Copy this zip's `.github/workflows/backend-tests.yml` into your repo's
   existing `.github/workflows/` folder (next to `selenium-tests.yml`).
3. Commit and push. The workflow triggers automatically on push/PR, or
   you can run it manually from the **Actions** tab
   ("Backend Testing (Security + Load + Functional API)" → **Run workflow**).

No changes to `backend/` itself are required for the suite to run.

## 2. What you do NOT need to do

- You don't need to run pytest, k6, bandit, or anything else on your machine.
- You don't need a real PostgreSQL/Neon database. CI spins up the FastAPI
  app with `DATABASE_URL=sqlite:///./ci_test.db` — a throwaway file that
  only exists for the lifetime of the job. Your app's own
  `_auto_seed()` (in `backend/app/main.py`) then seeds it automatically
  with the same demo accounts your `selenium-tests` workflow already
  relies on (officer `9000000001`/`officer123`, admin
  `9000000003`/`admin123`, farmer `9000000002`/`farmer123`, etc).
- You don't need to add any test dependencies to `backend/requirements.txt`
  — test-only dependencies live in `backend-tests/requirements-test.txt`
  and are installed into a separate step.

## 3. Optional: GitHub secrets you can add

None are required to run the default (`ci-ephemeral`) mode. Optionally:

| Secret | Purpose | If not set |
|---|---|---|
| `CI_TEST_JWT_SECRET` | Overrides the ephemeral instance's `SECRET_KEY` | Falls back to a clearly-labelled dummy value, `ci-ephemeral-secret-do-not-reuse` — fine, since this database is destroyed after the job |

You do **not** need to add your real `SECRET_KEY`, database URL, or any
production credential as a GitHub secret for this suite — it deliberately
never touches production.

## 4. Running against something other than the CI-ephemeral instance

The workflow has a `workflow_dispatch` input **`target`**:

- **`ci-ephemeral`** (default) — spins up `backend/` fresh inside the
  runner with SQLite, seeds it automatically, tests that. Fully
  non-destructive, safe to run on every push.
- **`deployed`** — points the entire suite (functional tests, injection
  fuzzing, DAST, AND the k6 load test) at
  `https://krishiiq-6su1.onrender.com`. **This writes real data** (farms,
  crops, etc.) to whatever database that deployment uses, and a load test
  can degrade or exhaust a free-tier Render instance. Because of that,
  the workflow **refuses to run in `deployed` mode** unless you also type
  the exact confirmation string `yes-run-against-deployed` into the
  `confirm_deployed` input when triggering it manually. There is no
  automatic/scheduled way to hit the deployed URL — it's a manual,
  explicit, one-time opt-in every time.

**Recommendation:** always use `ci-ephemeral` for routine CI runs (every
push/PR). Only use `deployed` deliberately, sparingly, and ideally against
a staging clone rather than the real production Render URL.

## 5. The k6 stress stages (200 / 500 / 1000 VUs)

The **baseline** load test (100 VUs, 1 minute) always runs. The **stress**
stages (ramping 200 → 500 → 1000 VUs) are gated behind the
`run_stress_test` workflow input (default `false`) and — regardless of
what `target` you pick — **only ever execute against `ci-ephemeral`**.
This is intentional: 1000 concurrent users is enough to knock over a
single free-tier Render dyno, and there's no reason to risk that when the
whole point of stress testing is to find the breaking point of a
throwaway instance you don't mind crashing.

To run the full baseline+stress suite: trigger the workflow manually with
`run_stress_test: true`.

## 6. What the workflow produces

Every run uploads a single artifact bundle, **`backend-test-reports`**
(30-day retention), containing:

| File | What it is |
|---|---|
| `executive-summary.md` | One-page verdict + headline numbers, for a non-technical reader / your report's front page |
| `security-review.md` | Full findings write-up: description, evidence, impact, remediation, OWASP/CWE mapping |
| `performance-report.md` | k6 load-test metrics (RPS, avg/min/max, P95/P99, error rate) with a plain-language read |
| `backend-inventory.md` | Every backend module and what it does |
| `endpoint-inventory.xlsx` | Every API route, its auth requirement, and description |
| `findings.xlsx` | Every confirmed finding, spreadsheet form, colour-coded by severity, sortable/filterable |
| `test-cases.xlsx` | All 400+ structured test cases: ID, category, objective, preconditions, steps, test data, expected result, severity, **actual Pass/Fail status from this run** |
| `bandit-report.json` / `pip-audit-report.json` | Raw SAST output |
| `junit.xml`, `pytest-report.json` | Raw pytest output, if you want to feed it into another tool |
| `k6-summary.json` | Raw k6 metrics |
| `backend-server.log` | The ephemeral server's stdout/stderr, useful for debugging a failed run |

A condensed version of the same numbers is also posted directly to the
**Job Summary** tab of each workflow run, so you can see the headline
results without downloading anything.

## 7. Why the pipeline sometimes fails (by design)

The job is configured to **fail only when a Critical-severity finding is
confirmed** — everything else (High/Medium/Low findings, individual test
failures) is recorded and reported but does **not** fail the build,
matching the brief. As of the version of `backend/` this suite was built
against, the tests are written to actively probe for — and will report
as **Critical** if still present — issues including:

- **Self-assigned privilege escalation at registration** — `RegisterRequest.role`
  is accepted directly from an anonymous client and stored unmodified
  (`backend/app/schemas/auth.py` + `backend/app/api/auth.py`), so anyone
  can register as `officer` or `admin`.
- **`alg=none` / wrong-secret JWT forgery checks** — these should already
  fail safely; they exist as regression tests.

...alongside a broader set of **High/Medium** findings the suite may
surface (not build-breaking, but worth reading `security-review.md` for),
such as missing ownership checks on a couple of sensor/advisory
endpoints, the unauthenticated `/sensors/ingest` endpoint, and the
absence of login rate-limiting. **Read `security-review.md` from an
actual run** — this is a living test suite, not a fixed list, and results
reflect whatever state `backend/` is in when the workflow runs.

## 8. Suggested next steps / what to change in `backend/`

These are **suggestions based on what the test suite may report** — no
change is required for the suite itself to run. If `security-review.md`
confirms them on your run, in rough priority order:

1. **`backend/app/schemas/auth.py`** — remove the client-settable `role`
   field from `RegisterRequest`, or ignore/clamp it server-side to
   `UserRole.FARMER` in `backend/app/api/auth.py`'s `register()`.
2. **`backend/app/config.py`** — remove the `"dev-secret-key"` default for
   `SECRET_KEY`; fail fast at startup if it's unset (or still equals the
   known default) outside `ENVIRONMENT=development`.
3. **`backend/app/api/sensors.py`** — add the same
   `Farm.farmer_id == farmer.id` ownership filter used in
   `backend/app/api/farms.py` to `get_latest_sensor` and
   `get_sensor_history`.
4. **`backend/app/api/advisory.py`** — add a `farmer_id` ownership check
   to `mark_read()`.
5. **`backend/app/api/disease.py`** — the 404 branch in `detect_disease()`
   references an undefined `engine` name and returns internal debug
   fields (`logged_in_farmer_id`, `actual_farm_farmer_id`, `db_url`) —
   fix the `NameError` and strip those fields outside development.
6. Add rate limiting (e.g. `slowapi`) to `/api/v1/auth/login` and
   `/api/v1/auth/register`.
7. Add a small ASGI middleware setting standard security headers
   (`X-Content-Type-Options`, `X-Frame-Options`,
   `Strict-Transport-Security`, a `Content-Security-Policy`).

None of these require any change to this test suite — re-run the
workflow after making changes and `test-cases.xlsx` / `findings.xlsx`
will reflect the new state automatically.

## 9. Extending the suite

- **New payloads:** edit `backend-tests/tests/payloads.py` — every
  injection/validation test that imports from it picks up new entries
  automatically.
- **New test cases:** add a test function anywhere under
  `backend-tests/tests/test_*.py`. Give it a docstring using the
  `CATEGORY:` / `TITLE:` / `OBJECTIVE:` / `EXPECTED:` / `SEVERITY:` field
  format already used throughout — the report generator parses these
  automatically into `test-cases.xlsx`, no other wiring needed.
- **New findings:** call `record_finding(...)` (imported from `conftest`)
  from inside any test — see existing examples in `test_dast.py` /
  `test_business_logic.py` / `test_configuration.py`.
- **New endpoints:** add them to
  `backend-tests/reports/inventory_data.py`'s `ENDPOINT_INVENTORY` list
  so they show up in `backend-inventory.md` / `endpoint-inventory.xlsx`.

## 10. Local debugging (optional, not required)

If you ever do want to run this locally to debug a CI failure:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=sqlite:///./local_test.db uvicorn app.main:app --port 8000 &

cd ../backend-tests
pip install -r requirements-test.txt
API_BASE_URL=http://127.0.0.1:8000 pytest tests/ -q
python reports/generate_reports.py
```

k6 (optional, for the load test only): install from
<https://k6.io/docs/get-started/installation/>, then:

```bash
cd backend-tests
BASE_URL=http://127.0.0.1:8000 k6 run --summary-export=load/k6-summary.json load/k6-load-test.js
```
