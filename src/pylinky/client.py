"""Linky API client implementation."""

from __future__ import annotations

import ssl
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, timedelta
from typing import TYPE_CHECKING

import certifi
import httpx
import jwt

from .exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    InvalidTokenError,
    PRMAccessError,
    ServerError,
)
from .models import DataType, MeteringData

if TYPE_CHECKING:
    from types import TracebackType

BASE_URL = "https://conso.boris.sh/api"
DEFAULT_USER_AGENT = "pylinky"


def create_ssl_context() -> ssl.SSLContext:
    """Create an SSL context with certifi certificates.

    This function performs blocking I/O and should be called from
    a thread executor when used in async contexts.
    """
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(certifi.where())
    return ctx


def _extract_prms(token: str) -> list[str]:
    """Extract PRM list from JWT token."""
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
    except jwt.DecodeError as e:
        raise InvalidTokenError(f"Cannot decode token: {e}") from e

    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError("Token has no 'sub' claim")

    if isinstance(sub, str):
        prms = [sub]
    elif isinstance(sub, list):
        prms = sub
    else:
        raise InvalidTokenError("Token 'sub' claim is not a string or list")

    if not prms:
        raise InvalidTokenError("Token contains no PRMs")

    return prms


def _handle_response_error(response: httpx.Response) -> None:
    """Handle HTTP error responses."""
    if response.is_success:
        return

    try:
        body = response.json()
        message = body.get("error") or body.get("message")
    except Exception:
        body = response.text
        message = body if body else None

    if response.status_code == 400:
        raise BadRequestError(message, body)
    if response.status_code == 401:
        raise AuthenticationError(message, body)
    if response.status_code >= 500:
        raise ServerError(response.status_code, message, body)

    raise APIError(response.status_code, message, body)


class LinkyClient:
    """Synchronous client for the Conso API.

    Example:
        >>> with LinkyClient(token="your-jwt-token") as client:
        ...     data = client.get_daily_consumption()
        ...     for reading in data.interval_reading:
        ...         print(f"{reading.date}: {reading.value} Wh")
    """

    def __init__(
        self,
        token: str,
        *,
        prm: str | None = None,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Linky client.

        Args:
            token: JWT authentication token from conso.boris.sh
            prm: Specific PRM to use (optional, defaults to first PRM in token)
            user_agent: User-Agent header for API requests
            timeout: Request timeout in seconds
        """
        self._token = token
        self._user_agent = user_agent
        self._timeout = timeout
        self._client: httpx.Client | None = None

        self._prms = _extract_prms(token)

        if prm is not None:
            if prm not in self._prms:
                raise PRMAccessError(prm)
            self._prm = prm
        else:
            self._prm = self._prms[0]

    @property
    def prm(self) -> str:
        """Current PRM being used for requests."""
        return self._prm

    @property
    def prms(self) -> list[str]:
        """List of all PRMs accessible with the current token."""
        return self._prms.copy()

    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=BASE_URL,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "User-Agent": self._user_agent,
                    "Accept": "application/json",
                },
                timeout=self._timeout,
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> LinkyClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def _request(self, data_type: DataType, start: date, end: date) -> MeteringData:
        """Make a request to the API."""
        client = self._get_client()
        response = client.get(
            f"/{data_type}",
            params={
                "prm": self._prm,
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
        )
        _handle_response_error(response)
        return MeteringData.from_dict(response.json())

    @staticmethod
    def _default_dates() -> tuple[date, date]:
        """Return default date range (yesterday to today)."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        return yesterday, today

    def get_daily_consumption(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> MeteringData:
        """Get daily energy consumption.

        Args:
            start: Start date (inclusive), defaults to yesterday
            end: End date (exclusive), defaults to today

        Returns:
            MeteringData with readings in Wh
        """
        if start is None or end is None:
            default_start, default_end = self._default_dates()
            start = start or default_start
            end = end or default_end
        return self._request("daily_consumption", start, end)

    def get_consumption_load_curve(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> MeteringData:
        """Get consumption load curve (30-minute intervals).

        Args:
            start: Start date (inclusive), defaults to yesterday
            end: End date (exclusive), defaults to today

        Returns:
            MeteringData with readings in W (average power)
        """
        if start is None or end is None:
            default_start, default_end = self._default_dates()
            start = start or default_start
            end = end or default_end
        return self._request("consumption_load_curve", start, end)

    def get_max_power(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> MeteringData:
        """Get daily maximum power consumption.

        Args:
            start: Start date (inclusive), defaults to yesterday
            end: End date (exclusive), defaults to today

        Returns:
            MeteringData with readings in VA (max power)
        """
        if start is None or end is None:
            default_start, default_end = self._default_dates()
            start = start or default_start
            end = end or default_end
        return self._request("consumption_max_power", start, end)

    def get_daily_production(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> MeteringData:
        """Get daily energy production.

        Args:
            start: Start date (inclusive), defaults to yesterday
            end: End date (exclusive), defaults to today

        Returns:
            MeteringData with readings in Wh
        """
        if start is None or end is None:
            default_start, default_end = self._default_dates()
            start = start or default_start
            end = end or default_end
        return self._request("daily_production", start, end)

    def get_production_load_curve(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> MeteringData:
        """Get production load curve (30-minute intervals).

        Args:
            start: Start date (inclusive), defaults to yesterday
            end: End date (exclusive), defaults to today

        Returns:
            MeteringData with readings in W (average power)
        """
        if start is None or end is None:
            default_start, default_end = self._default_dates()
            start = start or default_start
            end = end or default_end
        return self._request("production_load_curve", start, end)


class AsyncLinkyClient:
    """Asynchronous client for the Conso API.

    Example:
        >>> async with AsyncLinkyClient(token="your-jwt-token") as client:
        ...     data = await client.get_daily_consumption()
        ...     for reading in data.interval_reading:
        ...         print(f"{reading.date}: {reading.value} Wh")

    For use in Home Assistant or other async frameworks that detect blocking calls,
    you should pre-create the SSL context in an executor:

        >>> import asyncio
        >>> from pylinky import AsyncLinkyClient, create_ssl_context
        >>>
        >>> async def main():
        ...     loop = asyncio.get_event_loop()
        ...     ssl_context = await loop.run_in_executor(None, create_ssl_context)
        ...     async with AsyncLinkyClient(token="...", ssl_context=ssl_context) as client:
        ...         data = await client.get_daily_consumption()
    """

    def __init__(
        self,
        token: str,
        *,
        prm: str | None = None,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: float = 30.0,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        """Initialize the async Linky client.

        Args:
            token: JWT authentication token from conso.boris.sh
            prm: Specific PRM to use (optional, defaults to first PRM in token)
            user_agent: User-Agent header for API requests
            timeout: Request timeout in seconds
            ssl_context: Pre-created SSL context (optional, avoids blocking I/O)
        """
        self._token = token
        self._user_agent = user_agent
        self._timeout = timeout
        self._ssl_context = ssl_context
        self._client: httpx.AsyncClient | None = None

        self._prms = _extract_prms(token)

        if prm is not None:
            if prm not in self._prms:
                raise PRMAccessError(prm)
            self._prm = prm
        else:
            self._prm = self._prms[0]

    @property
    def prm(self) -> str:
        """Current PRM being used for requests."""
        return self._prm

    @property
    def prms(self) -> list[str]:
        """List of all PRMs accessible with the current token."""
        return self._prms.copy()

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=BASE_URL,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "User-Agent": self._user_agent,
                    "Accept": "application/json",
                },
                timeout=self._timeout,
                verify=self._ssl_context if self._ssl_context else True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> AsyncLinkyClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def _request(self, data_type: DataType, start: date, end: date) -> MeteringData:
        """Make an async request to the API."""
        client = self._get_client()
        response = await client.get(
            f"/{data_type}",
            params={
                "prm": self._prm,
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
        )
        _handle_response_error(response)
        return MeteringData.from_dict(response.json())

    @staticmethod
    def _default_dates() -> tuple[date, date]:
        """Return default date range (yesterday to today)."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        return yesterday, today

    async def get_daily_consumption(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> MeteringData:
        """Get daily energy consumption.

        Args:
            start: Start date (inclusive), defaults to yesterday
            end: End date (exclusive), defaults to today

        Returns:
            MeteringData with readings in Wh
        """
        if start is None or end is None:
            default_start, default_end = self._default_dates()
            start = start or default_start
            end = end or default_end
        return await self._request("daily_consumption", start, end)

    async def get_consumption_load_curve(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> MeteringData:
        """Get consumption load curve (30-minute intervals).

        Args:
            start: Start date (inclusive), defaults to yesterday
            end: End date (exclusive), defaults to today

        Returns:
            MeteringData with readings in W (average power)
        """
        if start is None or end is None:
            default_start, default_end = self._default_dates()
            start = start or default_start
            end = end or default_end
        return await self._request("consumption_load_curve", start, end)

    async def get_max_power(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> MeteringData:
        """Get daily maximum power consumption.

        Args:
            start: Start date (inclusive), defaults to yesterday
            end: End date (exclusive), defaults to today

        Returns:
            MeteringData with readings in VA (max power)
        """
        if start is None or end is None:
            default_start, default_end = self._default_dates()
            start = start or default_start
            end = end or default_end
        return await self._request("consumption_max_power", start, end)

    async def get_daily_production(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> MeteringData:
        """Get daily energy production.

        Args:
            start: Start date (inclusive), defaults to yesterday
            end: End date (exclusive), defaults to today

        Returns:
            MeteringData with readings in Wh
        """
        if start is None or end is None:
            default_start, default_end = self._default_dates()
            start = start or default_start
            end = end or default_end
        return await self._request("daily_production", start, end)

    async def get_production_load_curve(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> MeteringData:
        """Get production load curve (30-minute intervals).

        Args:
            start: Start date (inclusive), defaults to yesterday
            end: End date (exclusive), defaults to today

        Returns:
            MeteringData with readings in W (average power)
        """
        if start is None or end is None:
            default_start, default_end = self._default_dates()
            start = start or default_start
            end = end or default_end
        return await self._request("production_load_curve", start, end)


@contextmanager
def linky_client(
    token: str,
    *,
    prm: str | None = None,
    user_agent: str = DEFAULT_USER_AGENT,
    timeout: float = 30.0,
) -> Iterator[LinkyClient]:
    """Context manager for creating a LinkyClient.

    This is a convenience function equivalent to using LinkyClient as a context manager.

    Example:
        >>> with linky_client(token="your-jwt-token") as client:
        ...     data = client.get_daily_consumption()
    """
    client = LinkyClient(token, prm=prm, user_agent=user_agent, timeout=timeout)
    try:
        yield client
    finally:
        client.close()
