# pylinky

Python client for the [Conso API](https://conso.boris.sh/) - Access your Linky smart meter data.

## Installation

```bash
pip install pylinky
```

## Quick Start

```python
from datetime import date
from pylinky import LinkyClient

# Get your token from https://conso.boris.sh/
with LinkyClient(token="your-jwt-token") as client:
    # Get daily consumption
    data = client.get_daily_consumption(
        start=date(2024, 1, 1),
        end=date(2024, 1, 8),
    )

    for reading in data.interval_reading:
        print(f"{reading.date}: {reading.value} Wh")

    print(f"Total: {data.total} Wh")
```

## Async Support

```python
import asyncio
from datetime import date
from pylinky import AsyncLinkyClient

async def main():
    async with AsyncLinkyClient(token="your-jwt-token") as client:
        data = await client.get_daily_consumption(
            start=date(2024, 1, 1),
            end=date(2024, 1, 8),
        )
        print(f"Total: {data.total} Wh")

asyncio.run(main())
```

## API Methods

### Consumption

- `get_daily_consumption(start, end)` - Daily energy consumption in Wh
- `get_consumption_load_curve(start, end)` - 30-minute interval power consumption in W
- `get_max_power(start, end)` - Daily maximum power in VA

### Production (for solar panels)

- `get_daily_production(start, end)` - Daily energy production in Wh
- `get_production_load_curve(start, end)` - 30-minute interval power production in W

## Multi-PRM Support

If your token grants access to multiple meters (PRMs), you can select which one to use:

```python
client = LinkyClient(token="your-token", prm="12345678901234")

# List all accessible PRMs
print(client.prms)  # ['12345678901234', '98765432109876']
```

## Data Models

### MeteringData

All API methods return a `MeteringData` object with:

- `usage_point_id` - The PRM identifier
- `start` / `end` - Date range
- `quality` - Data quality indicator
- `reading_type` - Metadata about units and aggregation
- `interval_reading` - Tuple of readings
- `total` - Sum of all reading values
- `average` - Average of all reading values

### IntervalReading

Each reading contains:

- `value` - The measurement value (int)
- `date` - The reading date
- `interval_length` - Duration for load curves (e.g., "PT30M")
- `measure_type` - Type indicator for max power readings

## Error Handling

```python
from pylinky import (
    LinkyClient,
    InvalidTokenError,
    PRMAccessError,
    AuthenticationError,
    BadRequestError,
    ServerError,
)

try:
    with LinkyClient(token="your-token") as client:
        data = client.get_daily_consumption()
except InvalidTokenError:
    print("Token format is invalid")
except PRMAccessError as e:
    print(f"Cannot access PRM: {e.prm}")
except AuthenticationError:
    print("Token expired or invalid")
except BadRequestError as e:
    print(f"Invalid request: {e}")
except ServerError:
    print("API server error, try again later")
```

## Home Assistant Integration

This library is designed for integration with Home Assistant. Example configuration:

```python
from datetime import date, timedelta
from pylinky import AsyncLinkyClient

async def get_yesterday_consumption(token: str) -> int:
    """Get yesterday's total consumption in Wh."""
    yesterday = date.today() - timedelta(days=1)
    today = date.today()

    async with AsyncLinkyClient(token=token) as client:
        data = await client.get_daily_consumption(start=yesterday, end=today)
        return data.total
```

## License

MIT
