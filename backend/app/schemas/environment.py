from typing import Optional
from pydantic import BaseModel, Field

class WeatherProfile(BaseModel):
    """
    Normalized internal IrrigaSense environmental profile.
    Values are extracted and cleaned from Open-Meteo API.
    """
    temperature_c: float = Field(..., description="Current 2m air temperature in Celsius")
    humidity_percent: float = Field(..., description="Current relative humidity percentage")
    precipitation_mm: float = Field(..., description="Current precipitation in millimeters")
    wind_speed_kmh: float = Field(..., description="Current 10m wind speed in km/h")
    et0_mm: float = Field(..., description="Daily reference evapotranspiration (ET₀ FAO-56) in millimeters")

class EnvironmentalResponse(BaseModel):
    """
    Response schema for GET /api/environment/weather.
    """
    latitude: float = Field(..., description="Latitude of the query location")
    longitude: float = Field(..., description="Longitude of the query location")
    weather: WeatherProfile = Field(..., description="Normalized weather parameters")
    source: str = Field(default="Open-Meteo", description="Data source identifier")

class SoilProfile(BaseModel):
    """
    Normalized internal IrrigaSense soil profile.
    Values are extracted and cleaned from ISRIC SoilGrids WCS (0-5cm depth).
    """
    ph: Optional[float] = Field(default=None, description="Soil pH in H2O (0-5cm depth)")
    nitrogen: Optional[float] = Field(default=None, description="Total nitrogen in g/kg (0-5cm depth)")
    organic_carbon: Optional[float] = Field(default=None, description="Soil organic carbon in g/kg (0-5cm depth)")
    sand_percent: Optional[float] = Field(default=None, description="Sand fraction percentage (0-5cm depth)")
    silt_percent: Optional[float] = Field(default=None, description="Silt fraction percentage (0-5cm depth)")
    clay_percent: Optional[float] = Field(default=None, description="Clay fraction percentage (0-5cm depth)")
    bulk_density: Optional[float] = Field(default=None, description="Bulk density of fine earth fraction in g/cm³ (0-5cm depth)")

class SoilResponse(BaseModel):
    """
    Response schema for GET /api/environment/soil.
    """
    latitude: float = Field(..., description="Latitude of the query location")
    longitude: float = Field(..., description="Longitude of the query location")
    soil: SoilProfile = Field(..., description="Normalized soil properties (0-5cm depth)")
    depth: str = Field(default="0-5cm", description="Depth layer used for soil property estimation")
    source: str = Field(default="ISRIC SoilGrids", description="Data source identifier")

