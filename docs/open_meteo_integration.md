# IrrigaSense — Open-Meteo Environmental Data Integration

This document outlines the environmental data integration implemented in **Milestone 6B**. When a farmer confirms a farm location (`state.data.location.location_confirmed === true`), the backend can retrieve real-time environmental and reference evapotranspiration ($ET_0$) data using Open-Meteo without requiring manual input.

---

## 1. Upstream Open-Meteo Endpoint

- **Base URL:** `https://api.open-meteo.com/v1/forecast`
- **Method:** `GET`
- **Authentication:** None required (Open-Meteo does not require an API key for development/non-commercial usage).
- **Timeouts:** Configured with a strict 10.0-second timeout to prevent API request hanging.

### Parameters Sent to Open-Meteo:
| Parameter | Value | Purpose |
| :--- | :--- | :--- |
| `latitude` | Decimal degrees (e.g., `18.155`) | Farm latitude (-90.0 to 90.0) |
| `longitude` | Decimal degrees (e.g., `74.58`) | Farm longitude (-180.0 to 180.0) |
| `current` | `temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m` | Real-time weather variables |
| `daily` | `et0_fao_evapotranspiration` | Daily FAO-56 reference evapotranspiration |
| `timezone` | `auto` | Automatically aligns timestamps to farm location |

---

## 2. Variables & Units

All raw variables from Open-Meteo are normalized into clean domain units:

| Variable | Open-Meteo Variable | Normalized Field | Unit | Description |
| :--- | :--- | :--- | :--- | :--- |
| Temperature | `current.temperature_2m` | `temperature_c` | °C (Celsius) | Ambient air temperature at 2 meters |
| Relative Humidity | `current.relative_humidity_2m` | `humidity_percent` | % | Relative humidity percentage at 2 meters |
| Precipitation | `current.precipitation` | `precipitation_mm` | mm | Current precipitation (rain/showers) |
| Wind Speed | `current.wind_speed_10m` | `wind_speed_kmh` | km/h | Wind speed measured at 10 meters |
| Reference Evapotranspiration | `daily.et0_fao_evapotranspiration[0]` | `et0_mm` | mm/day | FAO-56 Reference Evapotranspiration ($ET_0$) |

---

## 3. Normalized Internal Response Structure

The internal IrrigaSense environmental profile never exposes raw Open-Meteo JSON. Instead, the application normalizes data using Pydantic models:

```json
{
  "latitude": 18.155,
  "longitude": 74.58,
  "weather": {
    "temperature_c": 26.5,
    "humidity_percent": 60.0,
    "precipitation_mm": 0.0,
    "wind_speed_kmh": 4.9,
    "et0_mm": 5.75
  },
  "source": "Open-Meteo"
}
```

### Schema Definition
- `WeatherProfile`:
  - `temperature_c` (`float`): Rounded to 2 decimal places.
  - `humidity_percent` (`float`): Rounded to 2 decimal places.
  - `precipitation_mm` (`float`): Rounded to 2 decimal places.
  - `wind_speed_kmh` (`float`): Rounded to 2 decimal places.
  - `et0_mm` (`float`): Rounded to 2 decimal places.
- `EnvironmentalResponse`:
  - `latitude` (`float`): Query latitude.
  - `longitude` (`float`): Query longitude.
  - `weather` (`WeatherProfile`): Normalized weather metrics.
  - `source` (`str`): `"Open-Meteo"`.

---

## 4. Architecture & Service Separation

```
Client (Frontend / Service)
       ↓
GET /api/environment/weather?latitude=...&longitude=...
       ↓ [Route Layer: backend/app/routes/environment.py]
OpenMeteoService [backend/app/services/environment/open_meteo.py]
       ↓ [Validation & HTTP Client with 10s Timeout]
Open-Meteo Forecast API (https://api.open-meteo.com/v1/forecast)
       ↓ [Parse & Normalize variables]
WeatherProfile & EnvironmentalResponse
       ↓
Clean HTTP 200 JSON Response
```

- **Route Isolation:** The external HTTP request logic is never placed in the FastAPI route handler; it is encapsulated inside `OpenMeteoService`.
- **Decoupled Assessment Pipeline:** Environmental queries are exposed under `/api/environment/` and kept independent of `/api/assessments/`.

---

## 5. Location Validation & Error Handling

Before initiating any external network request, coordinates are validated:
- `latitude`: Must satisfy `-90.0 <= latitude <= 90.0`.
- `longitude`: Must satisfy `-180.0 <= longitude <= 180.0`.

### Error Mapping:
| Condition | Internal Exception | HTTP Status Code | Client Error Detail |
| :--- | :--- | :--- | :--- |
| Latitude or longitude out of bounds | `InvalidCoordinatesError` | `400 Bad Request` | `"Invalid latitude: ... Latitude must be between -90.0 and 90.0 degrees."` |
| Request exceeds 10s timeout | `OpenMeteoTimeoutError` | `504 Gateway Timeout` | `"Upstream weather service timed out. Please try again."` |
| Upstream network connection error | `OpenMeteoConnectionError` | `502 Bad Gateway` | `"Unable to retrieve weather data from upstream provider."` |
| Upstream non-2xx status code | `OpenMeteoAPIError` | `502 Bad Gateway` | `"Unable to retrieve weather data from upstream provider."` |
| Malformed payload or missing variables | `OpenMeteoParsingError` | `502 Bad Gateway` | `"Invalid or incomplete weather data received from upstream provider."` |

Internal stack traces and network implementation details are never exposed to clients.

---

## 6. Example API Request & Response

### Request
```http
GET /api/environment/weather?latitude=18.155&longitude=74.58 HTTP/1.1
Host: localhost:8000
Accept: application/json
```

### Successful Response (200 OK)
```json
{
  "latitude": 18.155,
  "longitude": 74.58,
  "weather": {
    "temperature_c": 26.5,
    "humidity_percent": 60.0,
    "precipitation_mm": 0.0,
    "wind_speed_kmh": 4.9,
    "et0_mm": 5.75
  },
  "source": "Open-Meteo"
}
```

---

## 7. Current Weather vs. Future Historical Data

- **Milestone 6B Focus:** Real-time current observations (`current`) and daily reference evapotranspiration (`daily.et0_fao_evapotranspiration`). This provides immediate environmental context for the farmer's confirmed field location.
- **Future Historical Data:** Historical weather series (such as past 30–90 day cumulative rainfall, historical GDD, or temperature trends from Open-Meteo Historical Weather API) are **not** implemented in Milestone 6B. They can be added as a separate service capability in later milestones when feature engineering for ANFIS or irrigation scheduling requires time-series historical weather.

---

## 8. Verification & Testing

1. **Unit Test Suite:** `backend/tests/test_environment.py` (19 test cases using mocked responses)
   - Coordinate validation (valid, invalid latitude, invalid longitude)
   - Normalization of temperature, humidity, precipitation, wind speed, and ET₀
   - Timeout handling, HTTP failure handling, malformed responses
2. **Manual Live Integration Test:** `backend/verify_open_meteo_live.py`
   - Executes live request against Open-Meteo for Baramati `(18.155, 74.58)`.
   - Run command: `.\venv\Scripts\python.exe verify_open_meteo_live.py 18.155 74.58`
