import os
from io import BytesIO
from typing import Optional, Dict, Any, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import rasterio
from pyproj import Transformer
from owslib.wcs import WebCoverageService

from app.schemas.environment import SoilProfile, SoilResponse
from app.services.environment.open_meteo import InvalidCoordinatesError, validate_coordinates

SOILGRIDS_WCS_BASE_URL = "https://maps.isric.org/mapserv?map=/map/{map_name}.map"
DEFAULT_WCS_VERSION = "1.0.0"
HOMOLOSINE_CRS_URI = "urn:ogc:def:crs:EPSG::152160"
HOMOLOSINE_PROJ4 = "+proj=igh +lat_0=0 +lon_0=0 +datum=WGS84 +units=m +no_defs"
DEFAULT_TIMEOUT_SECONDS = 15.0

class SoilGridsError(Exception):
    """Base exception for SoilGrids service errors."""
    pass

class SoilGridsTimeoutError(SoilGridsError):
    """Raised when request to SoilGrids WCS times out."""
    pass

class SoilGridsConnectionError(SoilGridsError):
    """Raised when unable to connect to SoilGrids WCS."""
    pass

class SoilGridsExtractionError(SoilGridsError):
    """Raised when unable to read or parse the coverage raster."""
    pass


# Soil property configuration mapping
# Property key -> (map_name, coverage_id, depth, raw_unit, target_unit, scale_factor)
SOIL_PROPERTIES_CONFIG = {
    "ph": {
        "map_name": "phh2o",
        "cov_id": "phh2o_0-5cm_mean",
        "depth": "0-5cm",
        "raw_unit": "pH*10",
        "target_unit": "pH",
        "scale_factor": 0.1,  # raw / 10.0
    },
    "nitrogen": {
        "map_name": "nitrogen",
        "cov_id": "nitrogen_0-5cm_mean",
        "depth": "0-5cm",
        "raw_unit": "cg/kg",
        "target_unit": "g/kg",
        "scale_factor": 0.01,  # raw / 100.0 (1 cg/kg = 0.01 g/kg)
    },
    "organic_carbon": {
        "map_name": "soc",
        "cov_id": "soc_0-5cm_mean",
        "depth": "0-5cm",
        "raw_unit": "dg/kg",
        "target_unit": "g/kg",
        "scale_factor": 0.1,  # raw / 10.0 (1 dg/kg = 0.1 g/kg)
    },
    "sand_percent": {
        "map_name": "sand",
        "cov_id": "sand_0-5cm_mean",
        "depth": "0-5cm",
        "raw_unit": "g/kg",
        "target_unit": "%",
        "scale_factor": 0.1,  # raw / 10.0 (1000 g/kg = 100%)
    },
    "silt_percent": {
        "map_name": "silt",
        "cov_id": "silt_0-5cm_mean",
        "depth": "0-5cm",
        "raw_unit": "g/kg",
        "target_unit": "%",
        "scale_factor": 0.1,  # raw / 10.0
    },
    "clay_percent": {
        "map_name": "clay",
        "cov_id": "clay_0-5cm_mean",
        "depth": "0-5cm",
        "raw_unit": "g/kg",
        "target_unit": "%",
        "scale_factor": 0.1,  # raw / 10.0
    },
    "bulk_density": {
        "map_name": "bdod",
        "cov_id": "bdod_0-5cm_mean",
        "depth": "0-5cm",
        "raw_unit": "cg/cm3",
        "target_unit": "g/cm3",
        "scale_factor": 0.01,  # raw / 100.0 (100 cg/cm3 = 1 g/cm3)
    },
}

def transform_to_homolosine(latitude: float, longitude: float) -> Tuple[float, float]:
    """
    Transforms WGS84 (EPSG:4326) coordinates (latitude, longitude)
    to Interrupted Goode Homolosine projected coordinates (x, y) used by SoilGrids WCS.
    """
    transformer = Transformer.from_crs(
        "EPSG:4326",
        HOMOLOSINE_PROJ4,
        always_xy=True,
    )
    x, y = transformer.transform(longitude, latitude)
    return float(x), float(y)


class SoilGridsService:
    """
    Production service for retrieving, parsing, and normalizing soil properties
    from ISRIC SoilGrids 1.0.0 Web Coverage Service (WCS).
    """
    def __init__(
        self,
        base_url_template: str = SOILGRIDS_WCS_BASE_URL,
        wcs_version: str = DEFAULT_WCS_VERSION,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        wcs_client_factory: Optional[Callable[[str], Any]] = None,
    ):
        self.base_url_template = base_url_template
        self.wcs_version = wcs_version
        self.timeout_seconds = timeout_seconds
        self._wcs_client_factory = wcs_client_factory or self._default_wcs_factory

    def _default_wcs_factory(self, url: str) -> WebCoverageService:
        try:
            return WebCoverageService(url, version=self.wcs_version, timeout=self.timeout_seconds)
        except Exception as e:
            raise SoilGridsConnectionError(f"Failed to connect to SoilGrids WCS at {url}: {str(e)}") from e

    def fetch_single_coverage_raw(
        self,
        property_key: str,
        x: float,
        y: float
    ) -> Optional[int]:
        """
        Executes a WCS 1.0.0 getCoverage request for a single property and extracts
        the raw raster integer value at (x, y). Returns None if nodata or unavailable.
        """
        cfg = SOIL_PROPERTIES_CONFIG[property_key]
        map_name = cfg["map_name"]
        cov_id = cfg["cov_id"]
        wcs_url = self.base_url_template.format(map_name=map_name)

        min_x, max_x = x - 250.0, x + 250.0
        min_y, max_y = y - 250.0, y + 250.0
        bbox = (min_x, min_y, max_x, max_y)

        try:
            wcs = self._wcs_client_factory(wcs_url)
            if cov_id not in wcs.contents:
                return None

            response = wcs.getCoverage(
                identifier=cov_id,
                crs=HOMOLOSINE_CRS_URI,
                bbox=bbox,
                resx=250,
                resy=250,
                format="GEOTIFF_INT16",
            )
            raw_bytes = response.read()

            with rasterio.open(BytesIO(raw_bytes)) as src:
                val_gen = src.sample([(x, y)])
                raw_val = next(val_gen)[0]
                nodata = src.nodata

                # SoilGrids uses -32768 or src.nodata for unmapped / water / urban cells
                if raw_val == nodata or raw_val == -32768:
                    return None
                return int(raw_val)

        except (SoilGridsConnectionError, SoilGridsTimeoutError):
            raise
        except Exception as e:
            err_str = str(e).lower()
            if "timed out" in err_str or "timeout" in err_str:
                raise SoilGridsTimeoutError(f"SoilGrids request timed out for property {property_key}: {e}") from e
            if "connection" in err_str or "failed to establish" in err_str:
                raise SoilGridsConnectionError(f"Failed to connect to SoilGrids for {property_key}: {e}") from e
            raise SoilGridsExtractionError(f"Failed to extract {property_key} from coverage: {e}") from e

    def normalize_property_value(
        self,
        property_key: str,
        raw_val: Optional[int]
    ) -> Optional[float]:
        """
        Converts raw raster integer into normalized application unit using documented scale factor.
        Returns None if raw_val is None (preserving missing data cleanly).
        """
        if raw_val is None:
            return None

        cfg = SOIL_PROPERTIES_CONFIG[property_key]
        scale_factor = cfg["scale_factor"]
        return round(float(raw_val * scale_factor), 2)

    def fetch_all_soil_properties(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, Optional[float]]:
        """
        Fetches and normalizes all 7 soil properties in parallel for maximum performance.
        """
        validate_coordinates(latitude, longitude)
        x, y = transform_to_homolosine(latitude, longitude)

        normalized_results: Dict[str, Optional[float]] = {}
        errors = []

        with ThreadPoolExecutor(max_workers=7) as executor:
            future_to_prop = {
                executor.submit(self.fetch_single_coverage_raw, prop, x, y): prop
                for prop in SOIL_PROPERTIES_CONFIG
            }

            for future in as_completed(future_to_prop):
                prop = future_to_prop[future]
                try:
                    raw_val = future.result()
                    normalized_val = self.normalize_property_value(prop, raw_val)
                    normalized_results[prop] = normalized_val
                except Exception as e:
                    errors.append(e)
                    normalized_results[prop] = None

        # If all 7 requests completely failed with network/timeout errors, propagate the error
        if len(errors) == len(SOIL_PROPERTIES_CONFIG):
            first_err = errors[0]
            if isinstance(first_err, (SoilGridsConnectionError, SoilGridsTimeoutError)):
                raise first_err
            raise SoilGridsError(f"Failed to fetch any soil coverage: {first_err}")

        return normalized_results

    def get_soil_profile(
        self,
        latitude: float,
        longitude: float
    ) -> SoilResponse:
        """
        High-level service entrypoint: validates coordinates, queries SoilGrids,
        normalizes values, and returns the canonical SoilResponse.
        """
        results = self.fetch_all_soil_properties(latitude, longitude)
        profile = SoilProfile(
            ph=results.get("ph"),
            nitrogen=results.get("nitrogen"),
            organic_carbon=results.get("organic_carbon"),
            sand_percent=results.get("sand_percent"),
            silt_percent=results.get("silt_percent"),
            clay_percent=results.get("clay_percent"),
            bulk_density=results.get("bulk_density"),
        )
        return SoilResponse(
            latitude=latitude,
            longitude=longitude,
            soil=profile,
            depth="0-5cm",
            source="ISRIC SoilGrids",
        )

# Global service instance
soilgrids_service = SoilGridsService()
