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
"""Single-copy fork configuration and durable operation descriptors."""

from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from opensandbox.models.sandboxes import NetworkPolicy


class ForkOverrides(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    env: dict[str, str | None] | None = None
    resource_limits: dict[str, str] | None = Field(None, alias="resourceLimits")
    resource_requests: dict[str, str] | None = Field(None, alias="resourceRequests")
    network_policy: NetworkPolicy | None = Field(None, alias="networkPolicy")
    metadata: dict[str, str] | None = None
    entrypoint: list[str] | None = Field(None, min_length=1)

    @model_validator(mode="after")
    def reject_null(self) -> "ForkOverrides":
        if any(getattr(self, key) is None for key in self.model_fields_set):
            raise ValueError("Omit fork overrides to inherit; null overrides are invalid.")
        return self


class ForkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timeout: timedelta
    overrides: ForkOverrides = Field(default_factory=lambda: ForkOverrides.model_validate({}))

    @model_validator(mode="after")
    def validate_timeout(self) -> "ForkRequest":
        seconds = self.timeout.total_seconds()
        if seconds < 60 or not seconds.is_integer():
            raise ValueError("Fork timeout must be whole seconds and at least 60 seconds.")
        return self

    def to_wire(self) -> dict:
        return {"timeout": int(self.timeout.total_seconds()),
                "overrides": self.overrides.model_dump(mode="json", by_alias=True, exclude_unset=True)}


class ForkStatus(BaseModel):
    state: Literal["Pending", "Snapshotting", "Provisioning", "Succeeded", "Failed"]
    reason: str | None = None
    message: str | None = None


class ForkOperation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    source_sandbox_id: str = Field(..., alias="sourceSandboxId")
    status: ForkStatus
    snapshot_id: str | None = Field(None, alias="snapshotId")
    sandbox_id: str | None = Field(None, alias="sandboxId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    cleanup_pending: bool = Field(False, alias="cleanupPending")


class ForkWaitTimeout(TimeoutError):
    """Waiting stopped locally; the operation continues on the server."""
    def __init__(self, fork_id: str) -> None:
        self.fork_id = fork_id
        super().__init__(f"Timed out waiting for fork {fork_id}; query get_fork to continue.")
