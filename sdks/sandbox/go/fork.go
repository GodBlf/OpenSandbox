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

package opensandbox

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"time"
)

// ForkOverrides replaces supplied fields; nil pointers inherit the source.
type ForkOverrides struct {
	Env              *map[string]*string `json:"env,omitempty"`
	ResourceLimits   *ResourceLimits     `json:"resourceLimits,omitempty"`
	ResourceRequests *ResourceLimits     `json:"resourceRequests,omitempty"`
	NetworkPolicy    *NetworkPolicy      `json:"networkPolicy,omitempty"`
	Metadata         *map[string]string  `json:"metadata,omitempty"`
	Entrypoint       *[]string           `json:"entrypoint,omitempty"`
}

// ForkRequest captures one rootfs copy. Timeout is the target lifetime.
type ForkRequest struct {
	Timeout   time.Duration
	Overrides *ForkOverrides
}

type ForkStatus struct {
	State   string `json:"state"`
	Reason  string `json:"reason,omitempty"`
	Message string `json:"message,omitempty"`
}

type ForkOperation struct {
	ID              string     `json:"id"`
	SourceSandboxID string     `json:"sourceSandboxId"`
	SnapshotID      string     `json:"snapshotId,omitempty"`
	SandboxID       string     `json:"sandboxId,omitempty"`
	Status          ForkStatus `json:"status"`
	CreatedAt       time.Time  `json:"createdAt"`
	UpdatedAt       time.Time  `json:"updatedAt"`
	CleanupPending  bool       `json:"cleanupPending"`
}

// Fork submits an operation; retries can reuse the same tenant-scoped key.
func (c *LifecycleClient) Fork(ctx context.Context, sourceID string, request ForkRequest, idempotencyKey string) (*ForkOperation, error) {
	if request.Timeout < time.Minute || request.Timeout%time.Second != 0 {
		return nil, fmt.Errorf("fork timeout must be whole seconds and at least 60")
	}
	client := *c.Client
	client.headers = make(map[string]string, len(c.headers)+1)
	for key, value := range c.headers {
		client.headers[key] = value
	}
	if idempotencyKey != "" {
		client.headers["Idempotency-Key"] = idempotencyKey
	}
	body := struct {
		Timeout   int64          `json:"timeout"`
		Overrides *ForkOverrides `json:"overrides,omitempty"`
	}{int64(request.Timeout / time.Second), request.Overrides}
	var operation ForkOperation
	if err := client.doRequest(ctx, http.MethodPost, "/sandboxes/"+url.PathEscape(sourceID)+"/fork", body, &operation); err != nil {
		return nil, err
	}
	return &operation, nil
}

func (c *LifecycleClient) GetFork(ctx context.Context, forkID string) (*ForkOperation, error) {
	var operation ForkOperation
	if err := c.doRequest(ctx, http.MethodGet, "/forks/"+url.PathEscape(forkID), nil, &operation); err != nil {
		return nil, err
	}
	return &operation, nil
}

func (m *SandboxManager) Fork(ctx context.Context, sourceID string, request ForkRequest, idempotencyKey string) (*ForkOperation, error) {
	return m.lifecycle.Fork(ctx, sourceID, request, idempotencyKey)
}

func (m *SandboxManager) GetFork(ctx context.Context, forkID string) (*ForkOperation, error) {
	return m.lifecycle.GetFork(ctx, forkID)
}

// Fork submits one rootfs copy of this sandbox.
func (s *Sandbox) Fork(ctx context.Context, request ForkRequest, idempotencyKey string) (*ForkOperation, error) {
	return s.lifecycle.Fork(ctx, s.id, request, idempotencyKey)
}

// ForkWaitError contains the operation ID; cancelling a wait does not cancel it.
type ForkWaitError struct {
	ForkID string
	Err    error
}

func (e *ForkWaitError) Error() string {
	return fmt.Sprintf("waiting for fork %s: %v; the server operation continues", e.ForkID, e.Err)
}
func (e *ForkWaitError) Unwrap() error { return e.Err }

// WaitForFork returns either terminal state. Bound waiting with a context deadline.
func (m *SandboxManager) WaitForFork(ctx context.Context, forkID string, interval time.Duration) (*ForkOperation, error) {
	if interval <= 0 {
		return nil, fmt.Errorf("fork polling interval must be positive")
	}
	for {
		operation, err := m.GetFork(ctx, forkID)
		if err != nil {
			return nil, &ForkWaitError{forkID, err}
		}
		if operation.Status.State == "Succeeded" || operation.Status.State == "Failed" {
			return operation, nil
		}
		timer := time.NewTimer(interval)
		select {
		case <-ctx.Done():
			timer.Stop()
			return nil, &ForkWaitError{forkID, ctx.Err()}
		case <-timer.C:
		}
	}
}
