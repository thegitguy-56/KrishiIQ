# KrishiIQ Selenium E2E Test Framework

A complete **Selenium WebDriver** automation framework with Page Object Model, parallel execution, retry logic, and full reporting — integrated with **GitHub Actions CI/CD**.

## 📁 Structure

```
selenium-tests/
├── config.py               # Central config (URLs, credentials, timeouts)
├── conftest.py             # Pytest fixtures (driver, pages, auth sessions)
├── driver_factory.py       # WebDriver factory (Chrome / Firefox, headless)
├── test_data.py            # Test data framework (credentials, payloads, boundary values)
├── generate_reports.py     # Report generator (Excel, HTML dashboard, summary.md)
├── pytest.ini              # Pytest config (reruns, timeout, markers, logging)
├── requirements.txt        # Python dependencies
├── pages/
│   ├── base_page.py        # BasePage with all shared helpers
│   ├── login_page.py       # LoginPage POM
│   ├── dashboard_page.py   # DashboardPage POM
│   ├── farmers_page.py     # FarmersPage POM
│   ├── disease_alerts_page.py  # DiseaseAlertsPage POM
│   └── other_pages.py      # AnalyticsPage, MapPage, UnauthorizedPage
└── tests/
    ├── test_authentication.py           # 40 authentication tests
    ├── test_authorization.py            # 40 authorization tests
    ├── test_navigation.py               # 30 navigation tests
    ├── test_ui_validation.py            # 50 UI validation tests
    ├── test_forms_and_input.py          # 50 form + 40 input validation tests
    ├── test_crud_operations.py          # 50 CRUD operation tests
    └── test_error_session_a11y_responsive.py  # 20+20+20+20 tests
```

## 🧪 Test Distribution (400+ total)

| Module | Count |
|--------|-------|
| Authentication | 40 |
| Authorization | 40 |
| Navigation | 30 |
| UI Validation | 50 |
| Forms | 50 |
| Input Validation | 40 |
| CRUD Operations | 50 |
| Error Handling | 20 |
| Session Management | 20 |
| Accessibility | 20 |
| Responsive Design | 20 |
| **Total** | **400+** |

## 🚀 Running Locally

```bash
cd selenium-tests
pip install -r requirements.txt

# Run all tests (parallel, headless)
pytest tests/ -n 4

# Run a specific module
pytest tests/test_authentication.py -v

# Run specific marker
pytest tests/ -m "authentication and high" -v

# Against local dev server
BASE_URL=http://localhost:5173/KrishiIQ/ pytest tests/ -n 4

# Non-headless (show browser)
HEADLESS=false pytest tests/ -v

# Generate reports after run
python generate_reports.py
```

## 📊 Reports Generated

| File | Description |
|------|-------------|
| `reports/execution-report.html` | Pytest HTML report |
| `reports/dashboard.html` | Rich visual dashboard |
| `reports/Automation_Test_Report.xlsx` | Excel with 5 sheets |
| `reports/execution-results.json` | Raw JSON results |
| `reports/summary.md` | Markdown summary |
| `reports/screenshots/` | Failure screenshots |
| `reports/logs/` | Full execution logs |

## ⚙️ CI/CD

The workflow `.github/workflows/selenium-tests.yml`:
- Triggers on **every push** and **pull request**
- Installs Chrome + ChromeDriver automatically
- Runs all 400+ tests in **parallel** (4 workers)
- **Retries** flaky tests up to 2 times
- Uploads all reports as **artifacts** (30-day retention)
- Writes **GitHub Actions job summary** with pass/fail counts
- **Fails the workflow** only if pass rate drops below **95%**

## 🔧 Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `https://thegitguy-56.github.io/KrishiIQ/` | App under test |
| `HEADLESS` | `true` | Run browser headless |
| `BROWSER` | `chrome` | `chrome` or `firefox` |
| `OFFICER_PHONE` | `9000000001` | Officer login |
| `OFFICER_PASSWORD` | `officer123` | Officer password |
| `ADMIN_PHONE` | `9000000003` | Admin login |
| `ADMIN_PASSWORD` | `admin123` | Admin password |

## 🏷️ Pytest Markers

```bash
pytest tests/ -m authentication    # Auth tests only
pytest tests/ -m "high"            # High-priority tests
pytest tests/ -m "not responsive"  # Skip responsive tests
```
