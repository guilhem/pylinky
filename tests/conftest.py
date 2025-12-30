"""Test fixtures for pylinky tests."""

import jwt
import pytest


@pytest.fixture
def single_prm_token() -> str:
    """JWT token with a single PRM."""
    return jwt.encode({"sub": "12345678901234"}, "secret", algorithm="HS256")


@pytest.fixture
def multi_prm_token() -> str:
    """JWT token with multiple PRMs."""
    return jwt.encode(
        {"sub": ["12345678901234", "98765432109876"]},
        "secret",
        algorithm="HS256",
    )


@pytest.fixture
def daily_consumption_response() -> dict:
    """Sample daily consumption API response."""
    return {
        "usage_point_id": "12345678901234",
        "start": "2024-01-01",
        "end": "2024-01-04",
        "quality": "BRUT",
        "reading_type": {
            "unit": "Wh",
            "measurement_kind": "energy",
            "aggregate": "sum",
            "measuring_period": "P1D",
        },
        "interval_reading": [
            {"value": "11776", "date": "2024-01-01"},
            {"value": "14401", "date": "2024-01-02"},
            {"value": "12820", "date": "2024-01-03"},
        ],
    }


@pytest.fixture
def load_curve_response() -> dict:
    """Sample load curve API response."""
    return {
        "usage_point_id": "12345678901234",
        "start": "2024-01-01",
        "end": "2024-01-02",
        "quality": "BRUT",
        "reading_type": {
            "unit": "W",
            "measurement_kind": "power",
            "aggregate": "average",
        },
        "interval_reading": [
            {"value": "450", "date": "2024-01-01T00:00:00", "interval_length": "PT30M"},
            {"value": "380", "date": "2024-01-01T00:30:00", "interval_length": "PT30M"},
            {"value": "520", "date": "2024-01-01T01:00:00", "interval_length": "PT30M"},
        ],
    }


@pytest.fixture
def max_power_response() -> dict:
    """Sample max power API response."""
    return {
        "usage_point_id": "12345678901234",
        "start": "2024-01-01",
        "end": "2024-01-04",
        "quality": "BRUT",
        "reading_type": {
            "unit": "VA",
            "measurement_kind": "power",
            "aggregate": "maximum",
            "measuring_period": "P1D",
        },
        "interval_reading": [
            {"value": "6200", "date": "2024-01-01", "measure_type": "B"},
            {"value": "7100", "date": "2024-01-02", "measure_type": "B"},
            {"value": "5800", "date": "2024-01-03", "measure_type": "B"},
        ],
    }
