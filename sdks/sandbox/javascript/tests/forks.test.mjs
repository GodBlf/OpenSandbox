// Copyright 2026 The OpenSandbox Authors. Licensed under the Apache License, Version 2.0.
import assert from "node:assert/strict";
import test from "node:test";
import { ConnectionConfig, DefaultAdapterFactory, ForkWaitTimeout, SandboxManager } from "../dist/index.js";

const payload = {
  id: "fork-1", sourceSandboxId: "source", status: { state: "Pending" },
  createdAt: "2026-10-04T08:00:00Z", updatedAt: "2026-10-04T08:00:00Z", cleanupPending: false,
};

test("fork adapter maps timeout, empty overrides, dates and per-request retry key", async () => {
  const requests = [];
  const config = new ConnectionConfig({ domain: "api.test", apiKey: "tenant-key" });
  config._fetch = async (input, init) => {
    const request = new Request(input, init);
    requests.push(request);
    return Response.json(payload, { status: request.method === "POST" ? 202 : 200 });
  };
  const factory = new DefaultAdapterFactory();
  const { sandboxes } = factory.createLifecycleStack({ connectionConfig: config, lifecycleBaseUrl: config.getBaseUrl() });
  const result = await sandboxes.fork("source", { timeoutSeconds: 1800, overrides: { env: {} } }, "retry");
  assert.equal(result.id, "fork-1");
  assert.ok(result.createdAt instanceof Date);
  assert.equal(new URL(requests[0].url).pathname, "/v1/sandboxes/source/fork");
  assert.equal(requests[0].headers.get("Idempotency-Key"), "retry");
  assert.deepEqual(await requests[0].json(), { timeout: 1800, overrides: { env: {} } });
  await sandboxes.getFork(result.id);
  assert.equal(requests[1].headers.get("Idempotency-Key"), null);
});

test("wait timeout contains operation ID and never cancels the task", async () => {
  const manager = SandboxManager.create({ adapterFactory: {
    createLifecycleStack() { return { sandboxes: { async getFork() { return payload; } } }; },
  } });
  await assert.rejects(manager.waitForFork("fork-1", { timeoutSeconds: 0.001, pollingIntervalSeconds: 0.001 }),
    (error) => error instanceof ForkWaitTimeout && error.forkId === "fork-1");
  await manager.close();
});
