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

using OpenSandbox.Models;

namespace OpenSandbox.Services;

/// <summary>Optional fork capability for lifecycle adapters.</summary>
public interface IForkSandboxes
{
    Task<ForkOperation> ForkAsync(string sandboxId, ForkRequest request, string? idempotencyKey = null, CancellationToken cancellationToken = default);
    Task<ForkOperation> GetForkAsync(string forkId, CancellationToken cancellationToken = default);
}

/// <summary>Fork helpers that preserve compatibility with existing lifecycle adapters.</summary>
public static class SandboxesForkExtensions
{
    public static Task<ForkOperation> ForkAsync(this ISandboxes service, string sandboxId, ForkRequest request, string? idempotencyKey = null, CancellationToken cancellationToken = default)
        => RequireFork(service).ForkAsync(sandboxId, request, idempotencyKey, cancellationToken);

    public static Task<ForkOperation> GetForkAsync(this ISandboxes service, string forkId, CancellationToken cancellationToken = default)
        => RequireFork(service).GetForkAsync(forkId, cancellationToken);

    private static IForkSandboxes RequireFork(ISandboxes service)
        => service as IForkSandboxes ?? throw new NotSupportedException("This custom lifecycle adapter does not implement fork.");
}
