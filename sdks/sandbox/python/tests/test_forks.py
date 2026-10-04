# Copyright 2026 The OpenSandbox Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from opensandbox.adapters.sandboxes_adapter import SandboxesAdapter
from opensandbox.config import ConnectionConfig
from opensandbox.config.connection_sync import ConnectionConfigSync
from opensandbox.manager import SandboxManager
from opensandbox.models.forks import (
    ForkOperation,
    ForkOverrides,
    ForkRequest,
    ForkWaitTimeout,
)
from opensandbox.sync.adapters.sandboxes_adapter import SandboxesAdapterSync
from opensandbox.sync.manager import SandboxManagerSync

PAYLOAD = {"id": "fork-1", "sourceSandboxId": "source", "status": {"state": "Pending"},
           "createdAt": "2026-10-04T08:00:00Z", "updatedAt": "2026-10-04T08:00:00Z", "cleanupPending": False}


def test_timeout_and_empty_overrides_wire():
    request = ForkRequest(timeout=timedelta(minutes=30), overrides=ForkOverrides(env={}))
    assert request.to_wire() == {"timeout": 1800, "overrides": {"env": {}}}
    with pytest.raises(ValueError):
        ForkRequest(timeout=timedelta(seconds=59))
    with pytest.raises(ValueError):
        ForkOverrides(env=None)


@pytest.mark.asyncio
async def test_async_adapter_maps_generated_request_and_operation():
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(202 if request.method == "POST" else 200, json=PAYLOAD)
    transport = httpx.MockTransport(handler)
    adapter = SandboxesAdapter(ConnectionConfig(domain="example.test", transport=transport))
    operation = await adapter.fork("source", ForkRequest(timeout=timedelta(minutes=30)), "retry")
    assert operation.id == "fork-1"
    assert requests[0].url.path == "/v1/sandboxes/source/fork"
    assert requests[0].headers["Idempotency-Key"] == "retry"
    assert json.loads(requests[0].content)["timeout"] == 1800
    assert (await adapter.get_fork(operation.id)).status.state == "Pending"
    await transport.aclose()


def test_sync_adapter_maps_generated_request_and_operation():
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(202 if request.method == "POST" else 200, json=PAYLOAD)
    transport = httpx.MockTransport(handler)
    adapter = SandboxesAdapterSync(ConnectionConfigSync(domain="example.test", transport=transport))
    assert adapter.fork("source", ForkRequest(timeout=timedelta(minutes=30)), "retry").id == "fork-1"
    assert requests[0].headers["Idempotency-Key"] == "retry"
    assert adapter.get_fork("fork-1").status.state == "Pending"
    transport.close()


@pytest.mark.asyncio
async def test_wait_timeout_preserves_operation_id():
    service = SimpleNamespace(get_fork=AsyncMock(return_value=ForkOperation.model_validate(PAYLOAD)))
    manager = SandboxManager(service, ConnectionConfig(), diagnostics_service=Mock())
    with pytest.raises(ForkWaitTimeout) as caught:
        await manager.wait_for_fork("fork-1", timeout=timedelta(milliseconds=1), polling_interval=timedelta(milliseconds=1))
    assert caught.value.fork_id == "fork-1"


def test_sync_wait_returns_failed_operation_without_cleanup():
    payload = {**PAYLOAD, "status": {"state": "Failed", "reason": "FORK::SNAPSHOT_FAILED"}}
    service = SimpleNamespace(get_fork=Mock(return_value=ForkOperation.model_validate(payload)))
    manager = SandboxManagerSync(service, ConnectionConfigSync(), diagnostics_service=Mock())
    assert manager.wait_for_fork("fork-1").status.state == "Failed"
