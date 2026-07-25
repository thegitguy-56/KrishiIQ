# KrishiIQ Mobile E2E Test Suite (Appium + Flutter + Python)

This folder is a complete Android E2E automation framework for the KrishiIQ
Flutter app, built with **Appium + appium-flutter-driver + pytest**, run
entirely inside **GitHub Actions** (Android emulator). Nothing needs to run
on your machine.

> **Important — framework correction:** the KrishiIQ `mobile/` app is a
> **Flutter** app (`pubspec.yaml`, `lib/*.dart`), not React Native/Expo, and
> there is no `eas build` command in this repo. This suite therefore builds
> the app with `flutter build apk` and drives it with `appium-flutter-driver`
> (the correct Appium plugin for Flutter apps), not `UiAutomator2` alone.
> See `MOBILE_TESTING_SETUP.md` at the repo root for full details.

## Layout

```
mobile-tests/
├── conftest.py              # Appium session, retry, screenshot/log capture
├── pytest.ini                # markers, timeouts
├── requirements.txt
├── config/
│   ├── capabilities.py       # Appium desired capabilities
│   └── settings.py           # env-driven config (host, port, timeouts)
├── pages/                    # Page Object Model, one file per screen
├── data/
│   ├── test_data.py          # data factories (valid/invalid/boundary data)
│   └── test_case_catalog.py  # generates the 400+ test-case metadata matrix
├── tests/                    # 15 modules matching the required distribution
├── utils/
│   ├── logger.py
│   ├── retry.py
│   └── report_generator.py   # builds xlsx/html/json/summary after the run
├── scripts/
│   └── key_audit.py          # finds Flutter widgets still missing keys
└── reports/                  # test output (git-ignored, created at runtime)
```

## How the 400+ test cases work

Each module (`tests/test_authentication.py`, etc.) contains real Appium
flows built on the Page Object Model. To reach the required count per
module without padding with fake duplicates, each flow is **parametrized**
over a data catalog (`data/test_case_catalog.py`) of distinct inputs
(invalid phone formats, boundary password lengths, SQLi/XSS strings,
locales, network conditions, etc.) — every parametrized case is a real,
independently-executable pytest test with its own ID, own assertion, and
its own row in the final report. This mirrors how real QA suites reach
large counts: same user journey, systematically varied data.

Module → target count (as required):
Authentication 40, Authorization 30, Camera/Upload 40, Advisory/Profile 20,
Navigation 30, Dashboard 20, Forms 40, CRUD 40, Input Validation 40, Error
Handling 20, Session Management 20, Notifications 20, Offline Handling 20,
Accessibility 10, Responsive UI 10 → **410 total**.

Run `pytest --collect-only -q` locally in CI logs to see the exact count.

## Running (CI only, by design)

This suite is meant to run via `.github/workflows/android-e2e.yml`. See
`MOBILE_TESTING_SETUP.md` at the repo root for the one-time setup steps.
