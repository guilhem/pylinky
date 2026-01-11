"""Data models for the Conso API responses."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Literal


class MeasurementKind(str, Enum):
    """Type of measurement."""

    ENERGY = "energy"
    POWER = "power"


class Aggregate(str, Enum):
    """Aggregation method for the measurement."""

    SUM = "sum"
    AVERAGE = "average"
    MAXIMUM = "maximum"


@dataclass(frozen=True, slots=True)
class ReadingType:
    """Metadata about the type of reading."""

    unit: str
    measurement_kind: MeasurementKind
    aggregate: Aggregate
    measuring_period: str | None = None


@dataclass(frozen=True, slots=True)
class IntervalReading:
    """A single reading interval."""

    value: int
    date: date | datetime
    interval_length: str | None = None
    measure_type: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "IntervalReading":
        """Create an IntervalReading from API response data."""
        date_str = data["date"]
        # Handle both ISO format with T and space-separated format
        if "T" in date_str or " " in date_str:
            # Replace space with T for fromisoformat compatibility
            # Keep full datetime for load curve data (30-min intervals)
            parsed_date: date | datetime = datetime.fromisoformat(
                date_str.replace(" ", "T")
            )
        else:
            parsed_date = date.fromisoformat(date_str)

        return cls(
            value=int(data["value"]),
            date=parsed_date,
            interval_length=data.get("interval_length"),
            measure_type=data.get("measure_type"),
        )


@dataclass(frozen=True, slots=True)
class MeteringData:
    """Base response for all metering data endpoints."""

    usage_point_id: str
    start: date
    end: date
    quality: str
    reading_type: ReadingType
    interval_reading: tuple[IntervalReading, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MeteringData":
        """Create MeteringData from API response."""
        reading_type_data = data["reading_type"]
        reading_type = ReadingType(
            unit=reading_type_data["unit"],
            measurement_kind=MeasurementKind(reading_type_data["measurement_kind"]),
            aggregate=Aggregate(reading_type_data["aggregate"]),
            measuring_period=reading_type_data.get("measuring_period"),
        )

        readings = tuple(
            IntervalReading.from_dict(r) for r in data.get("interval_reading", [])
        )

        return cls(
            usage_point_id=data["usage_point_id"],
            start=date.fromisoformat(data["start"]),
            end=date.fromisoformat(data["end"]),
            quality=data["quality"],
            reading_type=reading_type,
            interval_reading=readings,
        )

    @property
    def total(self) -> int:
        """Calculate total value across all readings."""
        return sum(r.value for r in self.interval_reading)

    @property
    def average(self) -> float:
        """Calculate average value across all readings."""
        if not self.interval_reading:
            return 0.0
        return self.total / len(self.interval_reading)


# Type aliases for specific response types
EnergyData = MeteringData  # unit: Wh, aggregate: sum
PowerData = MeteringData  # unit: W, aggregate: average
MaxPowerData = MeteringData  # unit: VA, aggregate: maximum

DataType = Literal[
    "daily_consumption",
    "consumption_load_curve",
    "consumption_max_power",
    "daily_production",
    "production_load_curve",
]
