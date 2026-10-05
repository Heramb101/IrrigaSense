import httpx
from typing import Optional, Dict, Any
from app.schemas.environment import WeatherProfile, EnvironmentalResponse

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_TIMEOUT_SECONDS = 10.0

class OpenMeteoError(Exception):
    """Base exception for Open-Meteo service errors."""
    pass

class InvalidCoordinatesError(OpenMeteoError):
    """Raised when latitude or longitude is outside valid bounds."""
    pass

class OpenMeteoTimeoutError(OpenMeteoError):
    """Raised when the HTTP request to Open-Meteo times out."""
    pass

class OpenMeteoConnectionError(OpenMeteoError):
    """Raised when unable to establish connection to Open-Meteo."""
    pass

class OpenMeteoAPIError(OpenMeteoError):
    """Raised when Open-Meteo returns a non-2xx HTTP status code."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

class OpenMeteoParsingError(OpenMeteoError):
    """Raised when the Open-Meteo response structure is malformed or missing variables."""
    pass

def validate_coordinates(latitude: float, longitude: float) -> None:
    """
    Validates that latitude and longitude are valid decimal degrees.
    Latitude: [-90.0, 90.0]
    Longitude: [-180.0, 180.0]
    """
    if latitude is None or longitude is None:
        raise InvalidCoordinatesError("Latitude and longitude must both be provided.")
    
    if not (-90.0 <= latitude <= 90.0):
        raise InvalidCoordinatesError(
            f"Invalid latitude: {latitude}. Latitude must be between -90.0 and 90.0 degrees."
        )
    
    if not (-180.0 <= longitude <= 180.0):
        raise InvalidCoordinatesError(
            f"Invalid longitude: {longitude}. Longitude must be between -180.0 and 180.0 degrees."
        )

class OpenMeteoService:
    """
    Production service for fetching and normalizing real-time weather and ET₀ data
    from Open-Meteo API.
    """
    def __init__(
        self,
        base_url: str = OPEN_METEO_FORECAST_URL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        client: Optional[httpx.Client] = None,
    ):
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self._client = client

    def _get_client(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        return httpx.Client(timeout=self.timeout_seconds)

    def fetch_weather_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Executes HTTP request to Open-Meteo Forecast API with strict timeout handling.
        """
        validate_coordinates(latitude, longitude)

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            "daily": "et0_fao_evapotranspiration",
            "timezone": "auto",
        }

        try:
            # If a custom client was provided, use it directly (e.g. for testing); otherwise manage lifecycle
            if self._client is not None:
                response = self._client.get(self.base_url, params=params)
            else:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.get(self.base_url, params=params)

            if response.status_code >= 400:
                raise OpenMeteoAPIError(
                    f"Open-Meteo API error: status {response.status_code}",
                    status_code=response.status_code,
                )

            return response.json()

        except httpx.TimeoutException as e:
            raise OpenMeteoTimeoutError(
                f"Connection to Open-Meteo timed out after {self.timeout_seconds}s."
            ) from e
        except httpx.RequestError as e:
            raise OpenMeteoConnectionError(
                f"Failed to connect to Open-Meteo: {type(e).__name__}"
            ) from e
        except Exception as e:
            if isinstance(e, OpenMeteoError):
                raise
            raise OpenMeteoError(f"Unexpected error querying Open-Meteo: {str(e)}") from e

    def parse_weather_profile(self, data: Dict[str, Any]) -> WeatherProfile:
        """
        Parses and validates raw Open-Meteo JSON response into the normalized WeatherProfile model.
        """
        if not isinstance(data, dict):
            raise OpenMeteoParsingError("Response payload must be a JSON object.")

        current = data.get("current")
        if not isinstance(current, dict):
            raise OpenMeteoParsingError("Response missing 'current' object.")

        daily = data.get("daily")
        if not isinstance(daily, dict):
            raise OpenMeteoParsingError("Response missing 'daily' object.")

        # Extract current weather variables
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        precipitation = current.get("precipitation")
        wind_speed = current.get("wind_speed_10m")

        if temp is None or humidity is None or precipitation is None or wind_speed is None:
            raise OpenMeteoParsingError(
                "Missing one or more required current variables (temperature_2m, relative_humidity_2m, precipitation, wind_speed_10m)."
            )

        # Extract daily ET₀ (FAO-56 reference evapotranspiration in mm)
        et0_series = daily.get("et0_fao_evapotranspiration")
        if not isinstance(et0_series, list) or len(et0_series) == 0 or et0_series[0] is None:
            raise OpenMeteoParsingError(
                "Missing required daily variable: et0_fao_evapotranspiration."
            )

        try:
            return WeatherProfile(
                temperature_c=round(float(temp), 2),
                humidity_percent=round(float(humidity), 2),
                precipitation_mm=round(float(precipitation), 2),
                wind_speed_kmh=round(float(wind_speed), 2),
                et0_mm=round(float(et0_series[0]), 2),
            )
        except (ValueError, TypeError) as e:
            raise OpenMeteoParsingError(f"Unable to convert weather variables to float: {str(e)}") from e

    def get_weather_profile(self, latitude: float, longitude: float) -> EnvironmentalResponse:
        """
        High-level service entrypoint: validates coordinates, fetches data,
        normalizes values, and returns the canonical EnvironmentalResponse.
        """
        raw_data = self.fetch_weather_data(latitude, longitude)
        profile = self.parse_weather_profile(raw_data)
        return EnvironmentalResponse(
            latitude=latitude,
            longitude=longitude,
            weather=profile,
            source="Open-Meteo",
        )

# Global service instance
open_meteo_service = OpenMeteoService()
