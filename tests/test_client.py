"""Tests for the LinkyClient."""

from datetime import date

import pytest
from pytest_httpx import HTTPXMock

from pylinky import (
    AsyncLinkyClient,
    AuthenticationError,
    BadRequestError,
    InvalidTokenError,
    LinkyClient,
    MeteringData,
    PRMAccessError,
    ServerError,
    linky_client,
)


class TestTokenValidation:
    """Tests for JWT token validation."""

    def test_invalid_token_format(self) -> None:
        """Test that invalid JWT format raises InvalidTokenError."""
        with pytest.raises(InvalidTokenError, match="Cannot decode token"):
            LinkyClient("not-a-jwt")

    def test_token_without_sub(self) -> None:
        """Test that token without 'sub' claim raises InvalidTokenError."""
        import jwt

        token = jwt.encode({"foo": "bar"}, "secret", algorithm="HS256")
        with pytest.raises(InvalidTokenError, match="no 'sub' claim"):
            LinkyClient(token)

    def test_single_prm_token(self, single_prm_token: str) -> None:
        """Test that single PRM token is parsed correctly."""
        client = LinkyClient(single_prm_token)
        assert client.prm == "12345678901234"
        assert client.prms == ["12345678901234"]
        client.close()

    def test_multi_prm_token(self, multi_prm_token: str) -> None:
        """Test that multi-PRM token is parsed correctly."""
        client = LinkyClient(multi_prm_token)
        assert client.prm == "12345678901234"
        assert client.prms == ["12345678901234", "98765432109876"]
        client.close()

    def test_specific_prm_selection(self, multi_prm_token: str) -> None:
        """Test that specific PRM can be selected."""
        client = LinkyClient(multi_prm_token, prm="98765432109876")
        assert client.prm == "98765432109876"
        client.close()

    def test_invalid_prm_selection(self, single_prm_token: str) -> None:
        """Test that selecting an inaccessible PRM raises PRMAccessError."""
        with pytest.raises(PRMAccessError, match="99999999999999"):
            LinkyClient(single_prm_token, prm="99999999999999")


class TestLinkyClient:
    """Tests for the synchronous LinkyClient."""

    def test_context_manager(self, single_prm_token: str) -> None:
        """Test that client works as context manager."""
        with LinkyClient(single_prm_token) as client:
            assert client.prm == "12345678901234"

    def test_linky_client_helper(self, single_prm_token: str) -> None:
        """Test the linky_client context manager helper."""
        with linky_client(single_prm_token) as client:
            assert client.prm == "12345678901234"

    def test_get_daily_consumption(
        self,
        single_prm_token: str,
        daily_consumption_response: dict,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test getting daily consumption data."""
        httpx_mock.add_response(json=daily_consumption_response)

        with LinkyClient(single_prm_token) as client:
            data = client.get_daily_consumption(
                start=date(2024, 1, 1),
                end=date(2024, 1, 4),
            )

        assert isinstance(data, MeteringData)
        assert data.usage_point_id == "12345678901234"
        assert len(data.interval_reading) == 3
        assert data.interval_reading[0].value == 11776
        assert data.total == 38997
        assert data.reading_type.unit == "Wh"

    def test_get_load_curve(
        self,
        single_prm_token: str,
        load_curve_response: dict,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test getting load curve data."""
        httpx_mock.add_response(json=load_curve_response)

        with LinkyClient(single_prm_token) as client:
            data = client.get_consumption_load_curve(
                start=date(2024, 1, 1),
                end=date(2024, 1, 2),
            )

        assert isinstance(data, MeteringData)
        assert len(data.interval_reading) == 3
        assert data.interval_reading[0].interval_length == "PT30M"
        assert data.reading_type.unit == "W"

    def test_get_max_power(
        self,
        single_prm_token: str,
        max_power_response: dict,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test getting max power data."""
        httpx_mock.add_response(json=max_power_response)

        with LinkyClient(single_prm_token) as client:
            data = client.get_max_power(
                start=date(2024, 1, 1),
                end=date(2024, 1, 4),
            )

        assert isinstance(data, MeteringData)
        assert len(data.interval_reading) == 3
        assert data.interval_reading[0].measure_type == "B"
        assert data.reading_type.unit == "VA"

    def test_authentication_error(
        self,
        single_prm_token: str,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test that 401 response raises AuthenticationError."""
        httpx_mock.add_response(
            status_code=401,
            json={"error": "Invalid token"},
        )

        with LinkyClient(single_prm_token) as client:
            with pytest.raises(AuthenticationError, match="Invalid token"):
                client.get_daily_consumption(
                    start=date(2024, 1, 1),
                    end=date(2024, 1, 4),
                )

    def test_bad_request_error(
        self,
        single_prm_token: str,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test that 400 response raises BadRequestError."""
        httpx_mock.add_response(
            status_code=400,
            json={"error": "Start date should be before end date"},
        )

        with LinkyClient(single_prm_token) as client:
            with pytest.raises(BadRequestError, match="Start date should be before"):
                client.get_daily_consumption(
                    start=date(2024, 1, 4),
                    end=date(2024, 1, 1),
                )

    def test_server_error(
        self,
        single_prm_token: str,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test that 5xx response raises ServerError."""
        httpx_mock.add_response(status_code=500)

        with LinkyClient(single_prm_token) as client:
            with pytest.raises(ServerError):
                client.get_daily_consumption(
                    start=date(2024, 1, 1),
                    end=date(2024, 1, 4),
                )


class TestAsyncLinkyClient:
    """Tests for the asynchronous AsyncLinkyClient."""

    async def test_context_manager(self, single_prm_token: str) -> None:
        """Test that async client works as context manager."""
        async with AsyncLinkyClient(single_prm_token) as client:
            assert client.prm == "12345678901234"

    async def test_get_daily_consumption(
        self,
        single_prm_token: str,
        daily_consumption_response: dict,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test getting daily consumption data asynchronously."""
        httpx_mock.add_response(json=daily_consumption_response)

        async with AsyncLinkyClient(single_prm_token) as client:
            data = await client.get_daily_consumption(
                start=date(2024, 1, 1),
                end=date(2024, 1, 4),
            )

        assert isinstance(data, MeteringData)
        assert data.usage_point_id == "12345678901234"
        assert len(data.interval_reading) == 3

    async def test_authentication_error(
        self,
        single_prm_token: str,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test that 401 response raises AuthenticationError asynchronously."""
        httpx_mock.add_response(
            status_code=401,
            json={"error": "Invalid token"},
        )

        async with AsyncLinkyClient(single_prm_token) as client:
            with pytest.raises(AuthenticationError):
                await client.get_daily_consumption(
                    start=date(2024, 1, 1),
                    end=date(2024, 1, 4),
                )
