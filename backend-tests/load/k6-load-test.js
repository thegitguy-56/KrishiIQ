/*
 * KrishiIQ backend load test.
 *
 * Stages:
 *   - Baseline: 100 VUs sustained for 1 minute (always runs)
 *   - Stress:   ramping through 200 -> 500 -> 1000 VUs, 1 minute each
 *               (only runs when RUN_STRESS_TEST=true, see README.md)
 *
 * Target defaults to the ephemeral CI instance (http://127.0.0.1:8000).
 * Override with -e BASE_URL=... to point elsewhere -- see README.md for
 * the safety notes on load-testing the deployed Render instance.
 *
 * Run locally:
 *   k6 run --summary-export=load/k6-summary.json load/k6-load-test.js
 *
 * Run with stress stages:
 *   k6 run -e RUN_STRESS_TEST=true --summary-export=load/k6-summary.json load/k6-load-test.js
 */
import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";
const RUN_STRESS_TEST = (__ENV.RUN_STRESS_TEST || "false").toLowerCase() === "true";

const FARMER_PHONE = __ENV.FARMER_PHONE || "9000000002";
const FARMER_PASSWORD = __ENV.FARMER_PASSWORD || "farmer123";
const OFFICER_PHONE = __ENV.OFFICER_PHONE || "9000000001";
const OFFICER_PASSWORD = __ENV.OFFICER_PASSWORD || "officer123";

export const loginFailures = new Counter("login_failures");
export const readLatency = new Trend("read_endpoint_latency", true);

const baselineStage = { duration: "1m", target: 100 };
const stressStages = [
  { duration: "1m", target: 200 },
  { duration: "1m", target: 500 },
  { duration: "1m", target: 1000 },
  { duration: "30s", target: 0 },
];

export const options = {
  scenarios: {
    baseline: {
      executor: "constant-vus",
      vus: baselineStage.target,
      duration: baselineStage.duration,
      exec: "baselineScenario",
    },
    ...(RUN_STRESS_TEST
      ? {
          stress: {
            executor: "ramping-vus",
            startVUs: 0,
            stages: stressStages,
            exec: "stressScenario",
            startTime: "1m10s", // starts right after the baseline scenario finishes
          },
        }
      : {}),
  },
  thresholds: {
    http_req_duration: ["p(95)<3000"],
    http_req_failed: ["rate<0.1"],
  },
};

function loginFarmer() {
  const res = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ phone: FARMER_PHONE, password: FARMER_PASSWORD }),
    { headers: { "Content-Type": "application/json" }, tags: { name: "login" } }
  );
  const ok = check(res, { "login status 200": (r) => r.status === 200 });
  if (!ok) {
    loginFailures.add(1);
    return null;
  }
  return res.json("access_token");
}

function readMix(token) {
  const headers = { headers: { Authorization: `Bearer ${token}` } };

  let res = http.get(`${BASE_URL}/api/v1/farms/`, { ...headers, tags: { name: "list_farms" } });
  check(res, { "farms 200": (r) => r.status === 200 });
  readLatency.add(res.timings.duration);

  res = http.get(`${BASE_URL}/api/v1/history/summary`, { ...headers, tags: { name: "history_summary" } });
  check(res, { "history summary 200": (r) => r.status === 200 });
  readLatency.add(res.timings.duration);

  res = http.get(`${BASE_URL}/health`, { tags: { name: "health" } });
  check(res, { "health 200": (r) => r.status === 200 });
}

export function baselineScenario() {
  const token = loginFarmer();
  if (token) {
    readMix(token);
  }
  sleep(1);
}

export function stressScenario() {
  const token = loginFarmer();
  if (token) {
    readMix(token);
  } else {
    // Even a failed login still hits the DB (password hash lookup) -- keep
    // stressing the backend's auth path under load.
    http.get(`${BASE_URL}/health`, { tags: { name: "health" } });
  }
  sleep(0.5);
}

export function handleSummary(data) {
  return {
    "load/k6-summary.json": JSON.stringify(data, null, 2),
    stdout: textSummary(data),
  };
}

// Minimal inline text summary so `k6 run` output stays readable without
// pulling in the full k6-summary library.
function textSummary(data) {
  const m = data.metrics || {};
  const dur = (m.http_req_duration && m.http_req_duration.values) || {};
  const failed = (m.http_req_failed && m.http_req_failed.values) || {};
  const reqs = (m.http_reqs && m.http_reqs.values) || {};
  return [
    "=== KrishiIQ Load Test Summary ===",
    `Requests/sec: ${(reqs.rate || 0).toFixed(2)}`,
    `Avg: ${(dur.avg || 0).toFixed(1)}ms  Min: ${(dur.min || 0).toFixed(1)}ms  Max: ${(dur.max || 0).toFixed(1)}ms`,
    `P95: ${(dur["p(95)"] || 0).toFixed(1)}ms  P99: ${(dur["p(99)"] || 0).toFixed(1)}ms`,
    `Error rate: ${(((failed.rate || 0)) * 100).toFixed(2)}%`,
  ].join("\n");
}
