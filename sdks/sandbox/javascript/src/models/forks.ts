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

import type { components } from "../api/lifecycle.js";

export type ForkOverrides = components["schemas"]["ForkOverrides"];
export interface ForkRequest {
  /** Target lifetime in whole seconds, at least 60. */
  timeoutSeconds: number;
  overrides?: ForkOverrides;
}
export type ForkOperation = Omit<components["schemas"]["ForkOperation"], "createdAt" | "updatedAt"> & {
  createdAt: Date;
  updatedAt: Date;
};
export class ForkWaitTimeout extends Error {
  constructor(public readonly forkId: string) {
    super(`Timed out waiting for fork ${forkId}; the server operation continues.`);
    this.name = "ForkWaitTimeout";
  }
}
