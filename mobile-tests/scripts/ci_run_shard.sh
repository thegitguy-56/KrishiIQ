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
for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1:4723/wd/hub/status > /dev/null; then
    READY=1
    break
  fi
  echo "Waiting for Appium... ($i/30)"
  sleep 2
done

if [ "$READY" -ne 1 ]; then
  echo "::error::Appium server failed to start"
  kill "$APPIUM_PID" || true
  exit 1
fi

echo "== Running Appium test suite (shard ${SHARD}/4) =="
cd mobile-tests
mkdir -p reports/screenshots reports/logs
export APPIUM_PORT=4723
export APK_PATH="${APK_PATH}"
export APP_PACKAGE="${APP_PACKAGE}"

set +e
python3 -m pytest \
  --reruns 2 --reruns-delay 2 \
  --json-report --json-report-file="reports/execution-results-shard-${SHARD}.json" \
  --junitxml="reports/junit-shard-${SHARD}.xml" \
  --splits 4 --group "${SHARD}" \
  -v 2>&1 | tee "reports/pytest-output-shard-${SHARD}.log"
TEST_EXIT=${PIPESTATUS[0]}
set -e

kill "$APPIUM_PID" || true
exit $TEST_EXIT
