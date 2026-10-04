#
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
#

from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.fork_status import ForkStatus


T = TypeVar("T", bound="ForkOperation")


@_attrs_define
class ForkOperation:
    """
    Attributes:
        id (str):
        source_sandbox_id (str):
        status (ForkStatus):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        cleanup_pending (bool): Failed-operation resource cleanup is still being retried.
        snapshot_id (str | Unset): Persistent snapshot retained on success.
        sandbox_id (str | Unset): Target sandbox ID, published once its resource exists.
    """

    id: str
    source_sandbox_id: str
    status: ForkStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
    cleanup_pending: bool
    snapshot_id: str | Unset = UNSET
    sandbox_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        source_sandbox_id = self.source_sandbox_id

        status = self.status.to_dict()

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        cleanup_pending = self.cleanup_pending

        snapshot_id = self.snapshot_id

        sandbox_id = self.sandbox_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "sourceSandboxId": source_sandbox_id,
                "status": status,
                "createdAt": created_at,
                "updatedAt": updated_at,
                "cleanupPending": cleanup_pending,
            }
        )
        if snapshot_id is not UNSET:
            field_dict["snapshotId"] = snapshot_id
        if sandbox_id is not UNSET:
            field_dict["sandboxId"] = sandbox_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.fork_status import ForkStatus

        d = dict(src_dict)
        id = d.pop("id")

        source_sandbox_id = d.pop("sourceSandboxId")

        status = ForkStatus.from_dict(d.pop("status"))

        created_at = isoparse(d.pop("createdAt"))

        updated_at = isoparse(d.pop("updatedAt"))

        cleanup_pending = d.pop("cleanupPending")

        snapshot_id = d.pop("snapshotId", UNSET)

        sandbox_id = d.pop("sandboxId", UNSET)

        fork_operation = cls(
            id=id,
            source_sandbox_id=source_sandbox_id,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            cleanup_pending=cleanup_pending,
            snapshot_id=snapshot_id,
            sandbox_id=sandbox_id,
        )

        fork_operation.additional_properties = d
        return fork_operation

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
