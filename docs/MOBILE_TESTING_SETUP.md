# Mobile E2E Testing — Setup Guide

This describes exactly what's in the zip and what to change in your repo
to wire it up. Everything runs in GitHub Actions — nothing needs Appium,
an emulator, or Flutter installed on your machine.

## 0. Why this differs from the original brief

The brief assumed a React Native/Expo app built with `eas build`. Your
`mobile/` folder is actually a **Flutter** app. There is no `eas` anywhere
in the repo. Two consequences, both already handled in this delivery:

1. **Build command** is `flutter build apk`, not `eas build`.
2. **Automation tool** is `appium-flutter-driver` (an Appium 2 driver
   plugin purpose-built for Flutter), not plain UiAutomator2 — Flutter
   renders as a single native canvas, so UiAutomator2 alone cannot see
   individual widgets like buttons or text fields.

## 1. What's in the zip

```
├── mobile-tests/                    → put this at repo root, alongside mobile/
│   ├── (framework: conftest.py, pages/, tests/, data/, utils/, ...)
├── .github/workflows/android-e2e.yml → put this at repo root .github/workflows/
└── mobile-lib-changes/               → small, additive changes to mobile/
    ├── pubspec.yaml                  → adds flutter_driver as a dev dependency
    └── lib/
        ├── main_test.dart            → NEW file: test-only entrypoint
        └── screens/                  → 8 screens with ValueKeys added
```

## 2. Exactly what to change in your repo

### a) Copy the test framework in
```bash
# from your repo root
cp -r mobile-tests ./
cp .github/workflows/android-e2e.yml .github/workflows/
```

### b) Apply the small Flutter changes
```bash
cp mobile-lib-changes/pubspec.yaml mobile/pubspec.yaml
cp mobile-lib-changes/lib/main_test.dart mobile/lib/main_test.dart
cp mobile-lib-changes/lib/screens/*.dart mobile/lib/screens/
```
**What these changes actually do, so you can review them:**
- `pubspec.yaml`: adds `flutter_driver` under `dev_dependencies` only —
  doesn't touch your app's runtime dependencies.
- `lib/main_test.dart`: a **new, separate** entrypoint that calls
  `enableFlutterDriverExtension()` before running your existing `KrishiIQApp`.
  Your real `lib/main.dart` is **untouched** — production/Play Store builds
  are unaffected because they still build from `main.dart`.
- The 8 screen files each got `key: const ValueKey('...')` added to the
  interactive widgets the tests target (text fields, buttons, dropdowns).
  No logic, layout, or behavior was changed — only keys were added. Diff
  them against your originals before merging if you want to double check.

### c) Nothing else needs secrets or config for this to run
The workflow builds the test APK itself in CI and doesn't call your real
backend's production credentials — it uses the same seeded test accounts
your `selenium-tests.yml` already relies on (`FARMER_PHONE`/`FARMER_PASSWORD`
etc. in `mobile-tests/config/settings.py`). If your backend test-seed data
uses different phone numbers/passwords, update the defaults in
`mobile-tests/config/settings.py` (or set them as repo Variables/Secrets and
reference them as env vars in the workflow — the settings file already reads
from `os.getenv(...)` so this is a one-line addition per value if needed).

### d) Confirm your backend is reachable from the emulator in CI
The emulator talks to `10.0.2.2:8000` by convention (the emulator's alias
for the CI runner's `localhost`). If your backend job/service in CI binds
to a different host/port, update `BACKEND_BASE_URL` in
`mobile-tests/config/settings.py`, or point the app's build-time config at
it (check how `mobile/lib` currently resolves its API base URL — if it's
hardcoded per-environment, you may need a `--dart-define` added to the
`flutter build apk` step in the workflow).

### e) Push and watch the Actions tab
On push/PR/manual dispatch, `android-e2e.yml` will:
1. Build the debug test APK (`build-apk` job)
2. Fan out across **4 parallel emulators** (`mobile-e2e` matrix job, one
   AVD per shard — this is how parallelism works for mobile E2E; a single
   emulator can't safely run multiple Appium sessions at once, so we
   parallelize at the CI-runner level via `pytest-split` sharding instead
   of `pytest-xdist` within one device)
3. Merge all 4 shards' results and generate the reports (`report` job)
4. Upload everything as workflow artifacts (30-day retention) and post a
   summary table to the Actions run summary

## 3. Verifying the 400+ test count yourself

You don't need Appium for this — it's pure test collection:
```bash
cd mobile-tests
pip install -r requirements.txt
pytest --collect-only -q | tail -5
```
This delivery collects **404 tests** across the 15 required modules (see
`mobile-tests/README.md` for the exact per-module breakdown and how the
count is built honestly via parametrized data rather than padding).

## 4. Two things worth knowing before you present this

1. **Notifications module**: the app currently has a notification bell
   **icon** on Home, but its `onPressed` is an empty no-op — there's no
   `firebase_messaging`/push dependency and no `POST_NOTIFICATIONS`
   permission declared. The 20 Notifications tests validate what exists
   today (icon presence/tappability/no-crash) and are explicitly commented
   to be extended once the feature ships — they're not testing a feature
   that doesn't exist yet.
2. **CRUD module**: the farmer-facing app only exposes Create + Read for
   farms/farm-data/sensors. Update/Delete of those records is an
   officer/admin backend capability already covered by your
   `backend-tests.yml`. The CRUD tests document this and treat
   resubmission/overwrite as the closest farmer-facing "update" flow,
   rather than fabricating a delete button that doesn't exist in the UI.

## 5. If you want to extend coverage further

`mobile-tests/scripts/key_audit.py` scans any screen folder for
interactive widgets that still don't have a `ValueKey`, so you can see at
a glance what to instrument next:
```bash
python3 mobile-tests/scripts/key_audit.py mobile/lib/screens
```
