// Copyright 2026 The OpenSandbox Authors
// 
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import { ConnectionConfig, type ConnectionConfigOptions } from "./config/connection.js";
import { createDefaultAdapterFactory } from "./factory/defaultAdapterFactory.js";
import type { AdapterFactory } from "./factory/adapterFactory.js";

import type {
  CreateSnapshotRequest,
  ListSandboxesResponse,
  ListSnapshotsParams,
  ListSnapshotsResponse,
  SandboxId,
  SandboxInfo,
  SandboxMetadataPatch,
  SnapshotInfo,
} from "./models/sandboxes.js";
import type {
  CreateTemplateRequest,
  ListTemplatesParams,
  ListTemplatesResponse,
  TemplateInfo,
} from "./models/templates.js";
import type { Sandboxes } from "./services/sandboxes.js";
import { ForkWaitTimeout, type ForkRequest, type ForkOperation } from "./models/forks.js";

export interface SandboxManagerOptions {
  /**
   * Connection configuration for calling the OpenSandbox Lifecycle API.
   */
  connectionConfig?: ConnectionConfig | ConnectionConfigOptions;
  /**
   * Advanced override: inject a custom adapter factory (custom transports, dependency injection).
   */
  adapterFactory?: AdapterFactory;
}

export interface SandboxFilter {
  /**
   * Filter by sandbox lifecycle states.
   */
  states?: string[];
  /**
   * Filter by metadata key-value pairs.
   */
  metadata?: Record<string, string>;
  /**
   * Pagination page number (1-indexed).
   */
  page?: number;
  /**
   * Number of items per page.
   */
  pageSize?: number;
}

/**
 * Administrative interface for managing sandboxes (list/get/pause/resume/kill/renew).
 *
 * For interacting *inside* a sandbox, use {@link Sandbox}.
 */
export class SandboxManager {
  fork(sandboxId: string, request: ForkRequest, idempotencyKey?: string): Promise<ForkOperation> {
    return this.sandboxes.fork(sandboxId, request, idempotencyKey);
  }

  getFork(forkId: string): Promise<ForkOperation> {
    return this.sandboxes.getFork(forkId);
  }

  async waitForFork(forkId: string, opts: { timeoutSeconds?: number; pollingIntervalSeconds?: number } = {}): Promise<ForkOperation> {
    const timeout = opts.timeoutSeconds ?? 1800;
    const interval = opts.pollingIntervalSeconds ?? 2;
    if (!Number.isFinite(timeout) || !Number.isFinite(interval) || timeout <= 0 || interval <= 0) {
      throw new Error("Wait timeout and polling interval must be positive finite seconds.");
    }
    const deadline = performance.now() + timeout * 1000;
    while (true) {
      const operation = await this.getFork(forkId);
      if (operation.status.state === "Succeeded" || operation.status.state === "Failed") return operation;
      const remaining = deadline - performance.now();
      if (remaining <= 0) throw new ForkWaitTimeout(forkId);
      await new Promise((resolve) => setTimeout(resolve, Math.min(interval * 1000, remaining)));
    }
  }

  private readonly sandboxes: Sandboxes;
  private readonly connectionConfig: ConnectionConfig;
  /** True when this manager allocated (and may close) the transport. */
  private readonly ownsTransport: boolean;

  private constructor(opts: {
    sandboxes: Sandboxes;
    connectionConfig: ConnectionConfig;
    ownsTransport: boolean;
  }) {
    this.sandboxes = opts.sandboxes;
    this.connectionConfig = opts.connectionConfig;
    this.ownsTransport = opts.ownsTransport;
  }

  static create(opts: SandboxManagerOptions = {}): SandboxManager {
    const baseConnectionConfig = opts.connectionConfig instanceof ConnectionConfig
      ? opts.connectionConfig
      : new ConnectionConfig(opts.connectionConfig);
    const connectionConfig = baseConnectionConfig.withTransportIfMissing();
    // Caller-initialized transports are closed by their owner (mirrors Sandbox).
    const ownsTransport = connectionConfig !== baseConnectionConfig;
    const lifecycleBaseUrl = connectionConfig.getBaseUrl();
    const adapterFactory = opts.adapterFactory ?? createDefaultAdapterFactory();
    let sandboxes: Sandboxes;
    try {
      sandboxes = adapterFactory.createLifecycleStack({
        connectionConfig,
        lifecycleBaseUrl,
      }).sandboxes;
    } catch (err) {
      if (ownsTransport) {
        void connectionConfig.closeTransport().catch(() => undefined);
      }
      throw err;
    }
    return new SandboxManager({ sandboxes, connectionConfig, ownsTransport });
  }

  listSandboxInfos(filter: SandboxFilter = {}): Promise<ListSandboxesResponse> {
    return this.sandboxes.listSandboxes({
      states: filter.states,
      metadata: filter.metadata,
      page: filter.page,
      pageSize: filter.pageSize,
    });
  }

  getSandboxInfo(sandboxId: SandboxId): Promise<SandboxInfo> {
    return this.sandboxes.getSandbox(sandboxId);
  }

  patchSandboxMetadata(
    sandboxId: SandboxId,
    patch: SandboxMetadataPatch,
  ): Promise<SandboxInfo> {
    return this.sandboxes.patchSandboxMetadata(sandboxId, patch);
  }

  killSandbox(sandboxId: SandboxId, signal?: AbortSignal): Promise<void> {
    return this.sandboxes.deleteSandbox(sandboxId, signal);
  }

  pauseSandbox(sandboxId: SandboxId): Promise<void> {
    return this.sandboxes.pauseSandbox(sandboxId);
  }

  resumeSandbox(sandboxId: SandboxId): Promise<void> {
    return this.sandboxes.resumeSandbox(sandboxId);
  }

  /**
   * Renew expiration by setting expiresAt to now + timeoutSeconds.
   */
  async renewSandbox(sandboxId: SandboxId, timeoutSeconds: number): Promise<void> {
    const expiresAt = new Date(Date.now() + timeoutSeconds * 1000).toISOString();
    await this.sandboxes.renewSandboxExpiration(sandboxId, { expiresAt });
  }

  createSnapshot(sandboxId: SandboxId, req?: CreateSnapshotRequest): Promise<SnapshotInfo> {
    return this.sandboxes.createSnapshot(sandboxId, req);
  }

  getSnapshot(snapshotId: string): Promise<SnapshotInfo> {
    return this.sandboxes.getSnapshot(snapshotId);
  }

  listSnapshots(filter: ListSnapshotsParams = {}): Promise<ListSnapshotsResponse> {
    return this.sandboxes.listSnapshots(filter);
  }

  deleteSnapshot(snapshotId: string): Promise<void> {
    return this.sandboxes.deleteSnapshot(snapshotId);
  }

  /**
   * Create a fsb template (golden-image build).
   *
   * The build is asynchronous: the response starts at `status.phase: Pending`;
   * poll `getTemplate` until `Succeeded` (or `Failed`).
   */
  createTemplate(req: CreateTemplateRequest): Promise<TemplateInfo> {
    return this.sandboxes.createTemplate(req);
  }

  /**
   * Get a template with its latest build status by id.
   */
  getTemplate(templateId: string): Promise<TemplateInfo> {
    return this.sandboxes.getTemplate(templateId);
  }

  /**
   * List templates with metadata filtering and pagination options.
   */
  listTemplates(filter: ListTemplatesParams = {}): Promise<ListTemplatesResponse> {
    return this.sandboxes.listTemplates(filter);
  }

  /**
   * Delete a template by id. Running sandboxes are unaffected.
   */
  deleteTemplate(templateId: string): Promise<void> {
    return this.sandboxes.deleteTemplate(templateId);
  }

  /**
   * Release the HTTP agent resources allocated for this manager instance.
   *
   * Caller-initialized configs stay caller-owned — close them yourself via
   * `connectionConfig.closeTransport()`.
   */
  async close(): Promise<void> {
    // Shared (caller-initialized) transports are closed by their owner.
    if (this.ownsTransport) {
      await this.connectionConfig.closeTransport();
    }
  }
}
