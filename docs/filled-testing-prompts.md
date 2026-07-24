# Final Year Project — 3 Testing Prompts (Filled Version)

*Use these filled-out prompts with your AI coding agent (ChatGPT/Claude/etc) to generate the massive test suites.*

---

## PROMPT 1 — Web App Testing (Selenium)

```
ROLE
You are a Senior QA Automation Architect, Selenium Automation
Engineer, DevOps Engineer, SDET, Performance Engineer, and GitHub
Actions Specialist.

PROJECT CONTEXT
- Web app repo: https://github.com/thegitguy-56/KrishiIQ
- Frontend framework: React (Vite) + Tailwind CSS + React Router
- Base URL when running locally: http://localhost:5173/KrishiIQ/
- Base URL when deployed: https://thegitguy-56.github.io/KrishiIQ/
- Core modules/features in the app: Authentication (Login), Dashboard Overview (Stats, Water Usage, Crop Distribution, Yield Trends), Farmers List (CRUD), Interactive Farm Map (Leaflet), Disease Alerts (Filtering and Status updates), Analytics.

OBJECTIVE
Design and implement a complete end-to-end Selenium automation
framework and CI/CD pipeline that builds the app, deploys it (or
runs it locally in CI), executes the full Selenium E2E suite,
generates detailed reports, and publishes them automatically on
every push.

MANDATORY REQUIREMENTS
- Selenium WebDriver framework, Page Object Model
- Test Data Framework
- Parallel execution support
- Retry mechanism for flaky tests
- Explicit waits (no arbitrary sleeps)
- Screenshot capture on failure
- Full logging
- Minimum 400 executable test cases

TEST CASE DISTRIBUTION
- Authentication: 40
- Authorization: 40
- Navigation: 30
- UI Validation: 50
- Forms: 50
- CRUD Operations (Farmers/Alerts): 50
- Input Validation: 40
- Error Handling: 20
- Session Management: 20
- Accessibility: 20
- Responsive Design: 20
Total: 400+

Each test case must include: Test Case ID, Module, Priority,
Preconditions, Test Steps, Test Data, Expected Result, Actual
Result, Status.

REPORTING
Generate:
- Automation_Test_Report.xlsx (sheets: Executed Tests, Passed,
  Failed, Skipped, Execution Metrics, Defect Summary)
- execution-report.html and dashboard.html
- execution-results.json
- summary.md
- screenshots/ and logs/ for every run

CI/CD (.github/workflows/selenium-tests.yml)
- Trigger on push, pull_request, workflow_dispatch
- Build the app, run tests headless, upload all reports and
  screenshots as artifacts (30-day retention) on every run —
  including failed runs
- Publish a GitHub Actions summary with total/passed/failed/skipped
  counts and pass percentage
- Fail the workflow only if pass rate drops below 95%

Use environment variables / GitHub Secrets for any test login
credentials — never hardcode them anywhere in the repo or workflow.
```

---

## PROMPT 2 — Mobile App Testing (Appium)

```
ROLE
You are a Senior Mobile QA Architect, Appium Automation Engineer,
Android Test Engineer, SDET, and CI/CD Specialist.

PROJECT CONTEXT
- Mobile app repo: https://github.com/thegitguy-56/KrishiIQ
- Mobile framework: React Native / Expo
- APK build command: eas build -p android --profile preview
- Core modules/features in the app: Authentication, Dashboard, Camera (Disease Detection image upload), Advisory Feed, AI Chat Assistant, Notifications, Weather Updates.

OBJECTIVE
Design and implement a complete Android E2E automation framework and
CI/CD pipeline that builds the APK, starts an emulator, installs the
app, runs the full Appium suite, generates detailed reports, and
publishes them automatically on every push.

MANDATORY REQUIREMENTS
- Appium framework, Page Object Model
- Test Data Framework
- Parallel execution support
- Retry mechanism for flaky tests
- Screenshot + device log capture on failure
- Minimum 400 executable test cases

TEST CASE DISTRIBUTION
- Authentication: 40
- Authorization: 30
- Camera / Upload: 40
- Advisory / Profile Management: 20
- Navigation: 30
- Dashboard: 20
- Forms: 40
- CRUD Operations: 40
- Input Validation: 40
- Error Handling: 20
- Session Management: 20
- Notifications: 20
- Offline Handling: 20
- Accessibility: 10
- Responsive UI: 10
Total: 400+

Each test case must include: Test Case ID, Module, Test Name,
Priority, Preconditions, Test Steps, Test Data, Expected Result,
Actual Result, Status.

REPORTING
Generate:
- Automation_Test_Report.xlsx (sheets: Executed Tests, Passed,
  Failed, Skipped, Execution Metrics, Defect Summary, Pass Rate
  Summary)
- execution-report.html and dashboard.html
- execution-results.json
- summary.md
- screenshots/ and logs/ (device + Appium logs) for every run

CI/CD (.github/workflows/android-e2e.yml)
- Trigger on push, pull_request, workflow_dispatch
- Stages: checkout → setup Java/Android SDK → build APK → start
  emulator → verify emulator readiness → install APK → start Appium
  server → run tests → generate reports → upload artifacts (30-day
  retention, even on failure) → publish GitHub Actions summary
- Fail the workflow only if emulator/APK/Appium startup fails, or
  pass rate drops below 95%

Use environment variables / GitHub Secrets for any test login
credentials — never hardcode them anywhere in the repo or workflow.
```

---

## PROMPT 3 — Backend Testing (Security + Load + Functional API)

```
ROLE
You are a Senior Application Security Engineer, Penetration Tester,
API Security Specialist, QA Automation Architect, Performance
Testing Engineer, and DevSecOps Engineer.

PROJECT CONTEXT
- Backend repo: https://github.com/thegitguy-56/KrishiIQ
- Backend framework: Python FastAPI with SQLAlchemy
- Base API URL when running locally: http://localhost:8000
- Base API URL when deployed: https://krishiiq-6su1.onrender.com
- Key endpoints: /api/v1/auth/*, /api/v1/dashboard/*, /api/v1/disease/*, /api/v1/ai/*, /api/v1/farms/*
- Authentication method: JWT (Bearer tokens)
- Database: PostgreSQL (Neon Tech)

OBJECTIVE
Perform a complete backend assessment (SAST + DAST + functional API
testing + load testing) of the project and generate an audit report
suitable for academic evaluation. Never modify or delete real data;
all dynamic testing must be non-destructive.

MINIMUM 400 STRUCTURED TEST CASES, DISTRIBUTED AS:
- Authentication Tests: 30+
- Authorization Tests: 40+
- Input Validation Tests: 40+
- Injection Tests (SQL/NoSQL/Command/Path Traversal/SSRF): 60+
- Business Logic Tests: 30+
- Configuration Tests (CORS, headers, debug mode, cookies): 30+
- Functional API Tests (CRUD, validation, error codes): 100+
- Performance Tests: 30+
- DAST Tests (auth bypass, IDOR, JWT tampering, rate limiting): 40+
Total: 400+

Each test case must include: Test Case ID, Category, Title,
Objective, Preconditions, Test Steps, Test Data, Expected Result,
Severity, Status.

For every security finding, map to OWASP Top 10 / CWE where
possible, and include: Finding ID, Severity (Critical/High/Medium/
Low), File Path or Endpoint, Description, Evidence, Impact,
Remediation.

LOAD TESTING (k6, JMeter, or Artillery)
- Baseline: 100 virtual users, running continuously for 1 minute
- Stress: 200 / 500 / 1000 users to find the failure point
- Report: requests per second, avg/min/max response time, P95/P99,
  error rate — with a plain-language interpretation of the results

OUTPUT FILES
- backend-inventory.md, endpoint-inventory.xlsx
- security-review.md, executive-summary.md
- performance-report.md
- findings.xlsx, test-cases.xlsx
- k6-load-test.js (or your chosen tool's script)

CI/CD (.github/workflows/backend-tests.yml)
- Trigger on push, pull_request, workflow_dispatch
- Run static analysis, functional API tests, and the load test
- Upload all reports as artifacts (30-day retention)
- Publish a GitHub Actions summary with findings count by severity
- Fail the pipeline only when Critical vulnerabilities are found

Use environment variables / GitHub Secrets for any test login
credentials — never hardcode them anywhere in the repo, workflow,
or this prompt.
```
