"""Tests for the data models."""

from datetime import date

import pytest

from pylinky import Aggregate, IntervalReading, MeasurementKind, MeteringData, ReadingType


class TestIntervalReading:
    """Tests for IntervalReading."""

    def test_from_dict_date_only(self) -> None:
        """Test parsing date without time."""
        reading = IntervalReading.from_dict({"value": "1234", "date": "2024-01-15"})
        assert reading.value == 1234
        assert reading.date == date(2024, 1, 15)
        assert reading.interval_length is None

    def test_from_dict_datetime(self) -> None:
        """Test parsing datetime string."""
        reading = IntervalReading.from_dict({
            "value": "456",
            "date": "2024-01-15T14:30:00",
            "interval_length": "PT30M",
        })
        assert reading.value == 456
        assert reading.date == date(2024, 1, 15)
        assert reading.interval_length == "PT30M"

    def test_from_dict_with_measure_type(self) -> None:
        """Test parsing with measure_type."""
        reading = IntervalReading.from_dict({
            "value": "7800",
            "date": "2024-01-15",
            "measure_type": "B",
        })
        assert reading.measure_type == "B"

    def test_immutable(self) -> None:
        """Test that IntervalReading is immutable."""
        reading = IntervalReading.from_dict({"value": "100", "date": "2024-01-15"})
        with pytest.raises(AttributeError):
            reading.value = 200  # type: ignore[misc]


class TestReadingType:
    """Tests for ReadingType."""

    def test_energy_reading_type(self) -> None:
        """Test energy reading type."""
        rt = ReadingType(
            unit="Wh",
            measurement_kind=MeasurementKind.ENERGY,
            aggregate=Aggregate.SUM,
            measuring_period="P1D",
        )
        assert rt.unit == "Wh"
        assert rt.measurement_kind == MeasurementKind.ENERGY
        assert rt.aggregate == Aggregate.SUM

    def test_power_reading_type(self) -> None:
        """Test power reading type without measuring_period."""
        rt = ReadingType(
            unit="W",
            measurement_kind=MeasurementKind.POWER,
            aggregate=Aggregate.AVERAGE,
        )
        assert rt.measuring_period is None


class TestMeteringData:
    """Tests for MeteringData."""

    def test_from_dict(self, daily_consumption_response: dict) -> None:
        """Test parsing full API response."""
        data = MeteringData.from_dict(daily_consumption_response)

        assert data.usage_point_id == "12345678901234"
        assert data.start == date(2024, 1, 1)
        assert data.end == date(2024, 1, 4)
        assert data.quality == "BRUT"
        assert len(data.interval_reading) == 3

    def test_total(self, daily_consumption_response: dict) -> None:
        """Test total calculation."""
        data = MeteringData.from_dict(daily_consumption_response)
        assert data.total == 11776 + 14401 + 12820

    def test_average(self, daily_consumption_response: dict) -> None:
        """Test average calculation."""
        data = MeteringData.from_dict(daily_consumption_response)
        expected = (11776 + 14401 + 12820) / 3
        assert data.average == expected

    def test_average_empty(self) -> None:
        """Test average with no readings."""
        response = {
            "usage_point_id": "12345678901234",
            "start": "2024-01-01",
            "end": "2024-01-02",
            "quality": "BRUT",
            "reading_type": {
                "unit": "Wh",
                "measurement_kind": "energy",
                "aggregate": "sum",
            },
            "interval_reading": [],
        }
        data = MeteringData.from_dict(response)
        assert data.average == 0.0

    def test_immutable(self, daily_consumption_response: dict) -> None:
        """Test that MeteringData is immutable."""
        data = MeteringData.from_dict(daily_consumption_response)
        with pytest.raises(AttributeError):
            data.quality = "AUTRE"  # type: ignore[misc]


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
