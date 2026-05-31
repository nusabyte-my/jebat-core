/**
 * Basic smoke tests for jebatcore npm package.
 * Run: node src/test.js
 */

const { findPython, isInstalled, bootstrap } = require("./bootstrap");
const { JebatMCPClient } = require("./mcp-client");

let passed = 0, failed = 0;

function assert(cond, msg) {
  if (cond) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.log(`  FAIL: ${msg}`); }
}

console.log("\n── jebatcore Smoke Tests ──────────────────\n");

// 1. Python detection
const py = findPython();
assert(py !== null, `Python found: ${py || "none"}`);

// 2. JebatMCPClient constructor
const client = new JebatMCPClient({ transport: "stdio" });
assert(client !== null, "JebatMCPClient constructed");
assert(client.transportType === "stdio", "Default transport is stdio");
assert(client.command === "jebat", "Default command is 'jebat'");

// 3. JebatMCPClient HTTP constructor
const httpClient = new JebatMCPClient({ transport: "http", url: "http://localhost:8100/mcp" });
assert(httpClient.transportType === "http", "HTTP transport type set");
assert(httpClient.url === "http://localhost:8100/mcp", "URL set correctly");

// 4. JebatMCPClient streamable-http constructor
const shttpClient = new JebatMCPClient({ transport: "streamable-http", url: "http://localhost:8100/mcp" });
assert(shttpClient.transportType === "streamable-http", "Streamable HTTP transport type set");

// 5. Bootstrap (non-destructive — just check python detection)
assert(typeof bootstrap === "function", "bootstrap function exported");
assert(typeof findPython === "function", "findPython function exported");
assert(typeof isInstalled === "function", "isInstalled function exported");

// 6. Disconnect without connection (should not crash)
client.disconnect().then(() => {
  assert(true, "Disconnect without connection doesn't crash");
  console.log(`\n── Results: ${passed} passed, ${failed} failed ────────\n`);
  process.exit(failed > 0 ? 1 : 0);
}).catch(err => {
  assert(false, `Disconnect error: ${err.message}`);
  console.log(`\n── Results: ${passed} passed, ${failed} failed ────────\n`);
  process.exit(1);
});