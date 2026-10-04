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
	"encoding/json"
	"net/http"
	"testing"
	"time"
)

func TestForkRequestMappingAndHeaderIsolation(t *testing.T) {
	calls := 0
	_, client := newLifecycleServer(t, func(w http.ResponseWriter, r *http.Request) {
		calls++
		if calls == 1 {
			if r.URL.Path != "/sandboxes/source/fork" || r.Header.Get("Idempotency-Key") != "retry" {
				t.Error("fork path/key missing")
			}
			var body map[string]json.RawMessage
			if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
				t.Fatal(err)
			}
			if string(body["timeout"]) != "1800" {
				t.Error("timeout must be seconds")
			}
			var overrides map[string]json.RawMessage
			json.Unmarshal(body["overrides"], &overrides)
			if string(overrides["env"]) != "{}" {
				t.Error("empty env override must not be omitted")
			}
		} else if r.Header.Get("Idempotency-Key") != "" {
			t.Error("key leaked into later requests")
		}
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"id":"fork-1","sourceSandboxId":"source","status":{"state":"Succeeded"},"createdAt":"2026-10-04T08:00:00Z","updatedAt":"2026-10-04T08:00:00Z","cleanupPending":false}`))
	})
	empty := map[string]*string{}
	operation, err := client.Fork(context.Background(), "source", ForkRequest{Timeout: 30 * time.Minute, Overrides: &ForkOverrides{Env: &empty}}, "retry")
	if err != nil || operation.ID != "fork-1" {
		t.Fatalf("fork: %v", err)
	}
	if _, err := client.GetFork(context.Background(), "fork-1"); err != nil {
		t.Fatal(err)
	}
}
