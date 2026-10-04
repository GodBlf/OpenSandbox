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
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.fork_overrides_env import ForkOverridesEnv
    from ..models.fork_overrides_metadata import ForkOverridesMetadata
    from ..models.network_policy import NetworkPolicy
    from ..models.resource_limits import ResourceLimits


T = TypeVar("T", bound="ForkOverrides")


@_attrs_define
class ForkOverrides:
    """Omitted fields inherit source settings. Supplied fields replace the entire
    field; null is rejected. Empty env or metadata clears user configuration.
    Entrypoint defaults to tail -f /dev/null rather than the source command.

        Attributes:
            env (ForkOverridesEnv | Unset):
            resource_limits (ResourceLimits | Unset): Runtime resource constraints as key-value pairs. Similar to Kubernetes
                resource specifications,
                allows flexible definition of resource limits. Common resource types include:
                - `cpu`: CPU allocation in millicores (e.g., "250m" for 0.25 CPU cores)
                - `memory`: Memory allocation in bytes or human-readable format (e.g., "512Mi", "1Gi")
                - `gpu`: Number of GPU devices (e.g., "1")

                New resource types can be added without API changes.
                 Example: {'cpu': '500m', 'memory': '512Mi', 'gpu': '1'}.
            resource_requests (ResourceLimits | Unset): Runtime resource constraints as key-value pairs. Similar to
                Kubernetes resource specifications,
                allows flexible definition of resource limits. Common resource types include:
                - `cpu`: CPU allocation in millicores (e.g., "250m" for 0.25 CPU cores)
                - `memory`: Memory allocation in bytes or human-readable format (e.g., "512Mi", "1Gi")
                - `gpu`: Number of GPU devices (e.g., "1")

                New resource types can be added without API changes.
                 Example: {'cpu': '500m', 'memory': '512Mi', 'gpu': '1'}.
            network_policy (NetworkPolicy | Unset): Egress network policy matching the sidecar `/policy` request body.
                If `defaultAction` is omitted, the sidecar defaults to "deny"; passing an empty
                object or null results in allow-all behavior at startup.
            metadata (ForkOverridesMetadata | Unset):
            entrypoint (list[str] | Unset):
    """

    env: ForkOverridesEnv | Unset = UNSET
    resource_limits: ResourceLimits | Unset = UNSET
    resource_requests: ResourceLimits | Unset = UNSET
    network_policy: NetworkPolicy | Unset = UNSET
    metadata: ForkOverridesMetadata | Unset = UNSET
    entrypoint: list[str] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        env: dict[str, Any] | Unset = UNSET
        if not isinstance(self.env, Unset):
            env = self.env.to_dict()

        resource_limits: dict[str, Any] | Unset = UNSET
        if not isinstance(self.resource_limits, Unset):
            resource_limits = self.resource_limits.to_dict()

        resource_requests: dict[str, Any] | Unset = UNSET
        if not isinstance(self.resource_requests, Unset):
            resource_requests = self.resource_requests.to_dict()

        network_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.network_policy, Unset):
            network_policy = self.network_policy.to_dict()

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        entrypoint: list[str] | Unset = UNSET
        if not isinstance(self.entrypoint, Unset):
            entrypoint = self.entrypoint

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if env is not UNSET:
            field_dict["env"] = env
        if resource_limits is not UNSET:
            field_dict["resourceLimits"] = resource_limits
        if resource_requests is not UNSET:
            field_dict["resourceRequests"] = resource_requests
        if network_policy is not UNSET:
            field_dict["networkPolicy"] = network_policy
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if entrypoint is not UNSET:
            field_dict["entrypoint"] = entrypoint

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.fork_overrides_env import ForkOverridesEnv
        from ..models.fork_overrides_metadata import ForkOverridesMetadata
        from ..models.network_policy import NetworkPolicy
        from ..models.resource_limits import ResourceLimits

        d = dict(src_dict)
        _env = d.pop("env", UNSET)
        env: ForkOverridesEnv | Unset
        if isinstance(_env, Unset):
            env = UNSET
        else:
            env = ForkOverridesEnv.from_dict(_env)

        _resource_limits = d.pop("resourceLimits", UNSET)
        resource_limits: ResourceLimits | Unset
        if isinstance(_resource_limits, Unset):
            resource_limits = UNSET
        else:
            resource_limits = ResourceLimits.from_dict(_resource_limits)

        _resource_requests = d.pop("resourceRequests", UNSET)
        resource_requests: ResourceLimits | Unset
        if isinstance(_resource_requests, Unset):
            resource_requests = UNSET
        else:
            resource_requests = ResourceLimits.from_dict(_resource_requests)

        _network_policy = d.pop("networkPolicy", UNSET)
        network_policy: NetworkPolicy | Unset
        if isinstance(_network_policy, Unset):
            network_policy = UNSET
        else:
            network_policy = NetworkPolicy.from_dict(_network_policy)

        _metadata = d.pop("metadata", UNSET)
        metadata: ForkOverridesMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = ForkOverridesMetadata.from_dict(_metadata)

        entrypoint = cast(list[str], d.pop("entrypoint", UNSET))

        fork_overrides = cls(
            env=env,
            resource_limits=resource_limits,
            resource_requests=resource_requests,
            network_policy=network_policy,
            metadata=metadata,
            entrypoint=entrypoint,
        )

        return fork_overrides
