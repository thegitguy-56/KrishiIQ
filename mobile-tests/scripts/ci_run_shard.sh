#!/usr/bin/env bash
# Runs everything needed on the booted emulator for one CI shard:
# verify device, install APK, start Appium, wait for it, run pytest,
# tear down. Invoked as a single line from android-e2e.yml specifically
# because reactivecircus/android-emulator-runner executes each line of an
# inline `script:` block as its own separate `sh -c` call, which breaks
# multi-line constructs like `for`/`while` loops. Keeping the whole
# sequence in one real script file sidesteps that entirely.
set -e

SHARD="$1"
APK_PATH_REL="$2"
APP_PACKAGE="$3"

# Resolve to an absolute path up front. The Appium server resolves the
# `appium:app` capability relative to ITS OWN working directory (repo
# root, since it's started before we `cd mobile-tests` below), while the
# pytest client would need it relative to mobile-tests/. An absolute path
# sidesteps the mismatch entirely, regardless of which process resolves it.
APK_PATH="$(cd "$(dirname "${APK_PATH_REL}")" && pwd)/$(basename "${APK_PATH_REL}")"
echo "Resolved absolute APK path: ${APK_PATH}"

echo "== Verifying emulator readiness =="
adb wait-for-device
adb shell 'while [[ -z $(getprop sys.boot_completed) ]]; do sleep 1; done;'
adb devices

echo "== Installing APK =="
adb install -r "${APK_PATH}"

echo "== Starting Appium server =="
appium --base-path /wd/hub --log appium-server.log --log-level info &
APPIUM_PID=$!

READY=0
# Poll up to 90 s (45 × 2 s) for the Appium /status endpoint.
# The Flutter Observatory handshake with the emulator typically adds
# several seconds after the HTTP server itself reports ready; the
# extra headroom reduces the race condition that caused the session-
# create timeout to fail entire shards in earlier CI runs.
for i in $(seq 1 45); do
  if curl -sf http://127.0.0.1:4723/wd/hub/status > /dev/null; then
    READY=1
    break
  fi
  echo "Waiting for Appium... ($i/45)"
  sleep 2
done

if [ "$READY" -ne 1 ]; then
  echo "::error::Appium server failed to start within 90 s"
  echo "--- Last 40 lines of appium-server.log ---"
  tail -n 40 ../appium-server.log 2>/dev/null || true
  kill "$APPIUM_PID" || true
  exit 1
fi

# Give the Flutter Observatory one extra moment to bind after the
# /status endpoint goes green — without this, the very first
# NEW_SESSION request arrives before the driver plugin is fully ready
# and is the most common single-attempt timeout in this shard setup.
echo "Appium ready; waiting 2 s for Flutter Observatory to bind..."
sleep 2

echo "== Running Appium test suite (shard ${SHARD}/8) =="
cd mobile-tests
mkdir -p reports/screenshots reports/logs
export APPIUM_PORT=4723
export APK_PATH="${APK_PATH}"
export APP_PACKAGE="${APP_PACKAGE}"

set +e
python3 -m pytest \
  --reruns 1 --reruns-delay 2 --rerun-except="Timeout >" \
  --json-report --json-report-file="reports/execution-results-shard-${SHARD}.json" \
  --junitxml="reports/junit-shard-${SHARD}.xml" \
  --splits 8 --group "${SHARD}" \
  -v 2>&1 | tee "reports/pytest-output-shard-${SHARD}.log"
TEST_EXIT=${PIPESTATUS[0]}
set -e

kill "$APPIUM_PID" || true
exit $TEST_EXIT