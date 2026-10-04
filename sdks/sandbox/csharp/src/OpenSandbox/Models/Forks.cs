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

namespace OpenSandbox.Models;

public sealed class ForkRequest
{
    public TimeSpan Timeout { get; set; }
    public ForkOverrides? Overrides { get; set; }
}

public sealed class ForkOverrides
{
    public Dictionary<string, string?>? Env { get; set; }
    public Dictionary<string, string>? ResourceLimits { get; set; }
    public Dictionary<string, string>? ResourceRequests { get; set; }
    public NetworkPolicy? NetworkPolicy { get; set; }
    public Dictionary<string, string>? Metadata { get; set; }
    public List<string>? Entrypoint { get; set; }
}

public sealed class ForkStatus
{
    public string State { get; set; } = string.Empty;
    public string? Reason { get; set; }
    public string? Message { get; set; }
}

public sealed class ForkOperation
{
    public string Id { get; set; } = string.Empty;
    public string SourceSandboxId { get; set; } = string.Empty;
    public string? SnapshotId { get; set; }
    public string? SandboxId { get; set; }
    public ForkStatus Status { get; set; } = new();
    public DateTimeOffset CreatedAt { get; set; }
    public DateTimeOffset UpdatedAt { get; set; }
    public bool CleanupPending { get; set; }
}

public sealed class ForkWaitTimeoutException : TimeoutException
{
    public string ForkId { get; }
    public ForkWaitTimeoutException(string forkId)
        : base($"Timed out waiting for fork {forkId}; the server operation continues.")
    { ForkId = forkId; }
}
