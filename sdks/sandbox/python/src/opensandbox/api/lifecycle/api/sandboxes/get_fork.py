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

from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.fork_operation import ForkOperation
from ...types import Response


def _get_kwargs(
    fork_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/forks/{fork_id}".format(
            fork_id=quote(str(fork_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | ForkOperation | None:
    if response.status_code == 200:
        response_200 = ForkOperation.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | ForkOperation]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    fork_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | ForkOperation]:
    """Get fork progress and result

    Args:
        fork_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ForkOperation]
    """

    kwargs = _get_kwargs(
        fork_id=fork_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    fork_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | ForkOperation | None:
    """Get fork progress and result

    Args:
        fork_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ForkOperation
    """

    return sync_detailed(
        fork_id=fork_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    fork_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | ForkOperation]:
    """Get fork progress and result

    Args:
        fork_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ForkOperation]
    """

    kwargs = _get_kwargs(
        fork_id=fork_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    fork_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | ForkOperation | None:
    """Get fork progress and result

    Args:
        fork_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ForkOperation
    """

    return (
        await asyncio_detailed(
            fork_id=fork_id,
            client=client,
        )
    ).parsed
