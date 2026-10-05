from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.environment import EnvironmentalResponse, SoilResponse
from app.services.environment.open_meteo import (
    open_meteo_service,
    InvalidCoordinatesError,
    OpenMeteoTimeoutError,
    OpenMeteoConnectionError,
    OpenMeteoAPIError,
    OpenMeteoParsingError,
    OpenMeteoError,
)
from app.services.environment.soilgrids import (
    soilgrids_service,
    SoilGridsError,
    SoilGridsTimeoutError,
    SoilGridsConnectionError,
    SoilGridsExtractionError,
)

router = APIRouter(
    prefix="/api/environment",
    tags=["Environment"]
)

@router.get(
    "/weather",
    response_model=EnvironmentalResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current environmental weather & ET₀ profile",
    description="Retrieves current weather (temperature, humidity, precipitation, wind speed) and reference evapotranspiration (ET₀ FAO-56) from Open-Meteo for the specified latitude and longitude."
)
def get_current_weather(
    latitude: float = Query(
        ...,
        description="Latitude in decimal degrees (-90.0 to 90.0)",
        examples=[18.155],
    ),
    longitude: float = Query(
        ...,
        description="Longitude in decimal degrees (-180.0 to 180.0)",
        examples=[74.58],
    ),
):
    try:
        return open_meteo_service.get_weather_profile(latitude, longitude)
    except InvalidCoordinatesError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except OpenMeteoTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Upstream weather service timed out. Please try again.",
        )
    except (OpenMeteoConnectionError, OpenMeteoAPIError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to retrieve weather data from upstream provider.",
        )
    except OpenMeteoParsingError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid or incomplete weather data received from upstream provider.",
        )
    except OpenMeteoError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Environmental service error.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing environmental request.",
        )

@router.get(
    "/soil",
    response_model=SoilResponse,
    status_code=status.HTTP_200_OK,
    summary="Get environmental soil profile from ISRIC SoilGrids",
    description="Retrieves and normalizes topsoil properties (pH, nitrogen, organic carbon, sand, silt, clay, bulk density) from ISRIC SoilGrids 1.0.0 WCS for the specified coordinates."
)
def get_soil_profile(
    latitude: float = Query(
        ...,
        description="Latitude in decimal degrees (-90.0 to 90.0)",
        examples=[18.155],
    ),
    longitude: float = Query(
        ...,
        description="Longitude in decimal degrees (-180.0 to 180.0)",
        examples=[74.58],
    ),
):
    try:
        return soilgrids_service.get_soil_profile(latitude, longitude)
    except InvalidCoordinatesError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except SoilGridsTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Upstream SoilGrids service timed out. Please try again.",
        )
    except (SoilGridsConnectionError, SoilGridsExtractionError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to retrieve soil data from upstream SoilGrids provider.",
        )
    except SoilGridsError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="SoilGrids environmental service error.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing soil request.",
        )

