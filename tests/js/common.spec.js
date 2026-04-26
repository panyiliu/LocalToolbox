const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadCommonJs(fetchImpl, alertCollector = []) {
  const scriptPath = path.resolve(__dirname, "../../static/js/common.js");
  const script = fs.readFileSync(scriptPath, "utf8");
  const context = {
    fetch: fetchImpl,
    alert: (msg) => alertCollector.push(msg),
    window: {
      URL: {
        createObjectURL: () => "blob:mock",
        revokeObjectURL: () => {},
      },
    },
    document: {
      body: { appendChild: () => {}, removeChild: () => {} },
      createElement: () => ({ click: () => {} }),
    },
  };
  context.window.alert = context.alert;
  context.window.document = context.document;
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(script, context);
  return context.window.ToolboxApiClient;
}

test("parseApiResponse returns json data when success", async () => {
  const client = loadCommonJs(async () => {});
  const response = {
    headers: { get: () => "application/json" },
    json: async () => ({ success: true, data: { ok: true } }),
  };
  const result = await client.parseApiResponse(response);
  assert.equal(result.type, "json");
  assert.deepEqual(result.data, { ok: true });
});

test("parseApiResponse throws and alerts when json success false", async () => {
  const alerts = [];
  const client = loadCommonJs(async () => {}, alerts);
  const response = {
    headers: { get: () => "application/json" },
    json: async () => ({ success: false, message: "bad request" }),
  };
  await assert.rejects(() => client.parseApiResponse(response), /bad request/);
  assert.equal(alerts[0], "bad request");
});

test("extractFilename parses content-disposition filename*", () => {
  const client = loadCommonJs(async () => {});
  const filename = client.extractFilename("attachment; filename*=UTF-8''demo%20file.zip");
  assert.equal(filename, "demo file.zip");
});
