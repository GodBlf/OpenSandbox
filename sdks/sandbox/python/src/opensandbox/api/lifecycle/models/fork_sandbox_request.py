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

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.fork_overrides import ForkOverrides


T = TypeVar("T", bound="ForkSandboxRequest")


@_attrs_define
class ForkSandboxRequest:
    """
    Attributes:
        timeout (int): Target sandbox lifetime in seconds, subject to the server maximum.
        overrides (ForkOverrides | Unset): Omitted fields inherit source settings. Supplied fields replace the entire
            field; null is rejected. Empty env or metadata clears user configuration.
            Entrypoint defaults to tail -f /dev/null rather than the source command.
    """

    timeout: int
    overrides: ForkOverrides | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        timeout = self.timeout

        overrides: dict[str, Any] | Unset = UNSET
        if not isinstance(self.overrides, Unset):
            overrides = self.overrides.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "timeout": timeout,
            }
        )
        if overrides is not UNSET:
            field_dict["overrides"] = overrides

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.fork_overrides import ForkOverrides

        d = dict(src_dict)
        timeout = d.pop("timeout")

        _overrides = d.pop("overrides", UNSET)
        overrides: ForkOverrides | Unset
        if isinstance(_overrides, Unset):
            overrides = UNSET
        else:
            overrides = ForkOverrides.from_dict(_overrides)

        fork_sandbox_request = cls(
            timeout=timeout,
            overrides=overrides,
        )

        return fork_sandbox_request
