#!/usr/bin/env bash
# Prints the exact executable test count per module (pytest --collect-only,
# no Appium session needed) so CI can log/verify the 400+ requirement before
# spending emulator time running the full suite.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== Collecting mobile-tests (no execution) =="
python3 -m pytest --collect-only -q | tee /tmp/collect_output.txt

TOTAL=$(grep -Eo "^[0-9]+ tests? collected" /tmp/collect_output.txt | grep -Eo "^[0-9]+" || echo "0")
echo ""
echo "Total collected tests: ${TOTAL}"

if [ "${TOTAL}" -lt 400 ]; then
  echo "::warning::Collected test count (${TOTAL}) is below the required 400."
fi
