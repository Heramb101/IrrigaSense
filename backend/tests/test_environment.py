import pytest
from unittest.mock import patch, MagicMock
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.services.environment.open_meteo import (
    OpenMeteoService,
    validate_coordinates,
    InvalidCoordinatesError,
    OpenMeteoTimeoutError,
    OpenMeteoConnectionError,
    OpenMeteoAPIError,
    OpenMeteoParsingError,
)

client = TestClient(app)

MOCK_OPEN_METEO_PAYLOAD = {
    "latitude": 18.155,
    "longitude": 74.58,
    "generationtime_ms": 0.05,
    "utc_offset_seconds": 19800,
    "timezone": "Asia/Kolkata",
    "timezone_abbreviation": "IST",
    "elevation": 560.0,
    "current_units": {
        "time": "iso8601",
        "interval": "seconds",
        "temperature_2m": "°C",
        "relative_humidity_2m": "%",
        "precipitation": "mm",
        "wind_speed_10m": "km/h"
    },
    "current": {
        "time": "2026-10-02T23:30",
        "interval": 900,
        "temperature_2m": 28.1,
        "relative_humidity_2m": 81.0,
        "precipitation": 0.0,
        "wind_speed_10m": 6.5
    },
    "daily_units": {
        "time": "iso8601",
        "et0_fao_evapotranspiration": "mm"
    },
    "daily": {
        "time": ["2026-10-02"],
        "et0_fao_evapotranspiration": [3.02]
    }
}


# ==============================================================================
# 1. Valid Coordinates Test
# ==============================================================================
def test_valid_coordinates():
    # Service validation
    validate_coordinates(18.155, 74.58)
    validate_coordinates(-90.0, -180.0)
    validate_coordinates(90.0, 180.0)
    validate_coordinates(0.0, 0.0)


# ==============================================================================
# 2. Invalid Latitude Tests
# ==============================================================================
def test_invalid_latitude_service():
    with pytest.raises(InvalidCoordinatesError) as exc_info:
        validate_coordinates(90.1, 74.58)
    assert "Invalid latitude: 90.1" in str(exc_info.value)

    with pytest.raises(InvalidCoordinatesError) as exc_info2:
        validate_coordinates(-90.01, 74.58)
    assert "Invalid latitude: -90.01" in str(exc_info2.value)


def test_invalid_latitude_api():
    response = client.get("/api/environment/weather?latitude=91.0&longitude=74.58")
    assert response.status_code == 400
    assert "Invalid latitude" in response.json()["detail"]


# ==============================================================================
# 3. Invalid Longitude Tests
# ==============================================================================
def test_invalid_longitude_service():
    with pytest.raises(InvalidCoordinatesError) as exc_info:
        validate_coordinates(18.155, 180.5)
    assert "Invalid longitude: 180.5" in str(exc_info.value)

    with pytest.raises(InvalidCoordinatesError) as exc_info2:
        validate_coordinates(18.155, -180.1)
    assert "Invalid longitude: -180.1" in str(exc_info2.value)


def test_invalid_longitude_api():
    response = client.get("/api/environment/weather?latitude=18.155&longitude=181.0")
    assert response.status_code == 400
    assert "Invalid longitude" in response.json()["detail"]


# ==============================================================================
# 4. Successful Open-Meteo Response Test
# ==============================================================================
@patch("app.routes.environment.open_meteo_service.fetch_weather_data")
def test_successful_open_meteo_response(mock_fetch):
    mock_fetch.return_value = MOCK_OPEN_METEO_PAYLOAD

    response = client.get("/api/environment/weather?latitude=18.155&longitude=74.58")
    assert response.status_code == 200

    data = response.json()
    assert data["latitude"] == 18.155
    assert data["longitude"] == 74.58
    assert data["source"] == "Open-Meteo"
    assert "weather" in data

    weather = data["weather"]
    assert weather["temperature_c"] == 28.1
    assert weather["humidity_percent"] == 81.0
    assert weather["precipitation_mm"] == 0.0
    assert weather["wind_speed_kmh"] == 6.5
    assert weather["et0_mm"] == 3.02


# ==============================================================================
# 5. Temperature Normalization Test
# ==============================================================================
def test_temperature_normalization():
    service = OpenMeteoService()
    custom_payload = {
        "current": {
            "temperature_2m": 31.456,
            "relative_humidity_2m": 60,
            "precipitation": 1.2,
            "wind_speed_10m": 8.0,
        },
        "daily": {
            "et0_fao_evapotranspiration": [4.15],
        },
    }
    profile = service.parse_weather_profile(custom_payload)
    assert profile.temperature_c == 31.46


# ==============================================================================
# 6. Humidity Normalization Test
# ==============================================================================
def test_humidity_normalization():
    service = OpenMeteoService()
    custom_payload = {
        "current": {
            "temperature_2m": 25.0,
            "relative_humidity_2m": 72.8,
            "precipitation": 0.0,
            "wind_speed_10m": 5.0,
        },
        "daily": {
            "et0_fao_evapotranspiration": [3.5],
        },
    }
    profile = service.parse_weather_profile(custom_payload)
    assert profile.humidity_percent == 72.8


# ==============================================================================
# 7. Precipitation Normalization Test
# ==============================================================================
def test_precipitation_normalization():
    service = OpenMeteoService()
    custom_payload = {
        "current": {
            "temperature_2m": 22.0,
            "relative_humidity_2m": 90.0,
            "precipitation": 14.5,
            "wind_speed_10m": 12.0,
        },
        "daily": {
            "et0_fao_evapotranspiration": [2.1],
        },
    }
    profile = service.parse_weather_profile(custom_payload)
    assert profile.precipitation_mm == 14.5


# ==============================================================================
# 8. Wind Speed Normalization Test
# ==============================================================================
def test_wind_speed_normalization():
    service = OpenMeteoService()
    custom_payload = {
        "current": {
            "temperature_2m": 26.0,
            "relative_humidity_2m": 50.0,
            "precipitation": 0.0,
            "wind_speed_10m": 18.7,
        },
        "daily": {
            "et0_fao_evapotranspiration": [5.2],
        },
    }
    profile = service.parse_weather_profile(custom_payload)
    assert profile.wind_speed_kmh == 18.7


# ==============================================================================
# 9. Correct ET₀ Extraction Test
# ==============================================================================
def test_et0_extraction():
    service = OpenMeteoService()
    custom_payload = {
        "current": {
            "temperature_2m": 30.0,
            "relative_humidity_2m": 45.0,
            "precipitation": 0.0,
            "wind_speed_10m": 10.0,
        },
        "daily": {
            "et0_fao_evapotranspiration": [6.48, 5.9, 6.1],
        },
    }
    profile = service.parse_weather_profile(custom_payload)
    assert profile.et0_mm == 6.48


# ==============================================================================
# 10. Open-Meteo Timeout Test
# ==============================================================================
def test_open_meteo_timeout_service():
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.TimeoutException("Read timed out")
    service = OpenMeteoService(client=mock_client)

    with pytest.raises(OpenMeteoTimeoutError):
        service.fetch_weather_data(18.155, 74.58)


@patch("app.routes.environment.open_meteo_service.fetch_weather_data")
def test_open_meteo_timeout_api(mock_fetch):
    mock_fetch.side_effect = OpenMeteoTimeoutError("Request timed out")

    response = client.get("/api/environment/weather?latitude=18.155&longitude=74.58")
    assert response.status_code == 504
    assert "timed out" in response.json()["detail"].lower()


# ==============================================================================
# 11. Open-Meteo HTTP Failure Test
# ==============================================================================
def test_open_meteo_http_failure_service():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_client.get.return_value = mock_resp
    service = OpenMeteoService(client=mock_client)

    with pytest.raises(OpenMeteoAPIError) as exc_info:
        service.fetch_weather_data(18.155, 74.58)
    assert exc_info.value.status_code == 503


@patch("app.routes.environment.open_meteo_service.fetch_weather_data")
def test_open_meteo_http_failure_api(mock_fetch):
    mock_fetch.side_effect = OpenMeteoAPIError("Server error", status_code=500)

    response = client.get("/api/environment/weather?latitude=18.155&longitude=74.58")
    assert response.status_code == 502
    assert "Unable to retrieve weather data" in response.json()["detail"]


# ==============================================================================
# 12. Malformed API Response Tests
# ==============================================================================
def test_malformed_api_response_missing_current():
    service = OpenMeteoService()
    # Missing 'current' block
    payload = {"daily": {"et0_fao_evapotranspiration": [3.0]}}
    with pytest.raises(OpenMeteoParsingError) as exc_info:
        service.parse_weather_profile(payload)
    assert "missing 'current'" in str(exc_info.value).lower()


def test_malformed_api_response_missing_variable():
    service = OpenMeteoService()
    # Missing temperature_2m in current
    payload = {
        "current": {
            "relative_humidity_2m": 60,
            "precipitation": 0.0,
            "wind_speed_10m": 5.0,
        },
        "daily": {"et0_fao_evapotranspiration": [3.0]}
    }
    with pytest.raises(OpenMeteoParsingError) as exc_info:
        service.parse_weather_profile(payload)
    assert "missing one or more required current variables" in str(exc_info.value).lower()


def test_malformed_api_response_empty_et0():
    service = OpenMeteoService()
    # Empty et0_fao_evapotranspiration list
    payload = {
        "current": {
            "temperature_2m": 25.0,
            "relative_humidity_2m": 60,
            "precipitation": 0.0,
            "wind_speed_10m": 5.0,
        },
        "daily": {"et0_fao_evapotranspiration": []}
    }
    with pytest.raises(OpenMeteoParsingError) as exc_info:
        service.parse_weather_profile(payload)
    assert "missing required daily variable" in str(exc_info.value).lower()


@patch("app.routes.environment.open_meteo_service.fetch_weather_data")
def test_malformed_api_response_api(mock_fetch):
    mock_fetch.return_value = {"incomplete": "payload"}

    response = client.get("/api/environment/weather?latitude=18.155&longitude=74.58")
    assert response.status_code == 502
    assert "Invalid or incomplete weather data" in response.json()["detail"]
