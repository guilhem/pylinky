"""pylinky - Python client for the Conso API (Linky smart meter data)."""

from .client import AsyncLinkyClient, LinkyClient, create_ssl_context, linky_client
from .exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    InvalidTokenError,
    PRMAccessError,
    PyLinkyError,
    ServerError,
)
from .models import (
    Aggregate,
    DataType,
    EnergyData,
    IntervalReading,
    MaxPowerData,
    MeasurementKind,
    MeteringData,
    PowerData,
    ReadingType,
)

__version__ = "0.1.0"

__all__ = [
    # Clients
    "LinkyClient",
    "AsyncLinkyClient",
    "linky_client",
    "create_ssl_context",
    # Models
    "MeteringData",
    "IntervalReading",
    "ReadingType",
    "MeasurementKind",
    "Aggregate",
    "DataType",
    "EnergyData",
    "PowerData",
    "MaxPowerData",
    # Exceptions
    "PyLinkyError",
    "InvalidTokenError",
    "PRMAccessError",
    "APIError",
    "AuthenticationError",
    "BadRequestError",
    "ServerError",
]
