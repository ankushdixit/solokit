import http from "k6/http";
import { check, sleep } from "k6";
import { textSummary } from "https://jslib.k6.io/k6-summary/0.0.1/index.js";

/**
 * Generic Load Test
 * Tests performance under various load conditions
 */

export const options = {
  stages: [
    { duration: "30s", target: 20 }, // Ramp up to 20 users
    { duration: "1m", target: 20 }, // Stay at 20 users
    { duration: "30s", target: 50 }, // Spike to 50 users
    { duration: "1m", target: 50 }, // Stay at 50 users
    { duration: "30s", target: 0 }, // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"], // 95% of requests should be below 500ms
    http_req_failed: ["rate<0.01"], // Less than 1% of requests should fail
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:3000";

export default function () {
  // Test home page (all stacks have this)
  const homeRes = http.get(`${BASE_URL}/`);
  check(homeRes, {
    "home page status is 200": (r) => r.status === 200,
    "home page loads within 2s": (r) => r.timings.duration < 2000,
  });

  sleep(1);

  // Optional: Test additional routes if available
  // This will gracefully handle 404s for routes that don't exist
  const additionalRoutes = ["/dashboard", "/api/health"];

  for (const route of additionalRoutes) {
    const res = http.get(`${BASE_URL}${route}`, {
      tags: { name: route },
    });
    check(res, {
      [`${route} responds`]: (r) => r.status === 200 || r.status === 404,
    });
  }

  sleep(1);
}

// Summary handler
export function handleSummary(data) {
  return {
    stdout: textSummary(data, { indent: " ", enableColors: true }),
    "reports/load-test-summary.json": JSON.stringify(data),
  };
}
