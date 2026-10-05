import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.environment.soilgrids import (
    SoilGridsService,
    transform_to_homolosine,
    SoilGridsError,
    SoilGridsTimeoutError,
    SoilGridsConnectionError,
    SoilGridsExtractionError,
    SOIL_PROPERTIES_CONFIG,
)
from app.services.environment.open_meteo import InvalidCoordinatesError, validate_coordinates
from app.schemas.environment import SoilResponse, SoilProfile

client = TestClient(app)

MOCK_NORMALIZED_SOIL = {
    "ph": 7.2,
    "nitrogen": 1.21,
    "organic_carbon": 13.4,
    "sand_percent": 32.6,
    "silt_percent": 24.1,
    "clay_percent": 43.3,
    "bulk_density": 1.60,
}


# ==============================================================================
# 1. Valid Coordinates Test
# ==============================================================================
def test_valid_coordinates():
    validate_coordinates(18.155, 74.58)
    validate_coordinates(-90.0, -180.0)
    validate_coordinates(90.0, 180.0)
    validate_coordinates(0.0, 0.0)


# ==============================================================================
# 2. Invalid Latitude Tests
# ==============================================================================
def test_invalid_latitude_service():
    with pytest.raises(InvalidCoordinatesError) as exc_info:
        validate_coordinates(91.0, 74.58)
    assert "Invalid latitude: 91.0" in str(exc_info.value)

    with pytest.raises(InvalidCoordinatesError) as exc_info2:
        validate_coordinates(-90.5, 74.58)
    assert "Invalid latitude: -90.5" in str(exc_info2.value)


def test_invalid_latitude_api():
    response = client.get("/api/environment/soil?latitude=95.0&longitude=74.58")
    assert response.status_code == 400
    assert "Invalid latitude" in response.json()["detail"]


# ==============================================================================
# 3. Invalid Longitude Tests
# ==============================================================================
def test_invalid_longitude_service():
    with pytest.raises(InvalidCoordinatesError) as exc_info:
        validate_coordinates(18.155, 185.0)
    assert "Invalid longitude: 185.0" in str(exc_info.value)

    with pytest.raises(InvalidCoordinatesError) as exc_info2:
        validate_coordinates(18.155, -181.0)
    assert "Invalid longitude: -181.0" in str(exc_info2.value)


def test_invalid_longitude_api():
    response = client.get("/api/environment/soil?latitude=18.155&longitude=190.0")
    assert response.status_code == 400
    assert "Invalid longitude" in response.json()["detail"]


# ==============================================================================
# 4. Coordinate Transformation Test
# ==============================================================================
def test_coordinate_transformation():
    # Test coordinates transformation to Homolosine (x, y)
    lat, lon = 14.5, -14.5
    x, y = transform_to_homolosine(lat, lon)
    assert isinstance(x, float)
    assert isinstance(y, float)
    # Senegal coordinates in Homolosine are around x = -1456345, y = 1614132
    assert -1500000 < x < -1400000
    assert 1500000 < y < 1700000

    # Baramati (18.155, 74.58)
    bx, by = transform_to_homolosine(18.155, 74.58)
    assert 7900000 < bx < 8200000
    assert 1900000 < by < 2100000


# ==============================================================================
# 5. Successful pH Extraction Test
# ==============================================================================
def test_successful_ph_extraction():
    service = SoilGridsService()
    # Raw pH from SoilGrids is pH * 10
    raw_val = 72
    norm_val = service.normalize_property_value("ph", raw_val)
    assert norm_val == 7.2


# ==============================================================================
# 6. Successful Nitrogen Extraction Test
# ==============================================================================
def test_successful_nitrogen_extraction():
    service = SoilGridsService()
    # Raw nitrogen is in cg/kg -> convert to g/kg (divide by 100)
    raw_val = 121
    norm_val = service.normalize_property_value("nitrogen", raw_val)
    assert norm_val == 1.21


# ==============================================================================
# 7. Successful Organic Carbon Extraction Test
# ==============================================================================
def test_successful_organic_carbon_extraction():
    service = SoilGridsService()
    # Raw soc is in dg/kg -> convert to g/kg (divide by 10)
    raw_val = 134
    norm_val = service.normalize_property_value("organic_carbon", raw_val)
    assert norm_val == 13.4


# ==============================================================================
# 8. Successful Sand Extraction Test
# ==============================================================================
def test_successful_sand_extraction():
    service = SoilGridsService()
    # Raw sand is in g/kg -> convert to % (divide by 10)
    raw_val = 326
    norm_val = service.normalize_property_value("sand_percent", raw_val)
    assert norm_val == 32.6


# ==============================================================================
# 9. Successful Silt Extraction Test
# ==============================================================================
def test_successful_silt_extraction():
    service = SoilGridsService()
    # Raw silt is in g/kg -> convert to % (divide by 10)
    raw_val = 241
    norm_val = service.normalize_property_value("silt_percent", raw_val)
    assert norm_val == 24.1


# ==============================================================================
# 10. Successful Clay Extraction Test
# ==============================================================================
def test_successful_clay_extraction():
    service = SoilGridsService()
    # Raw clay is in g/kg -> convert to % (divide by 10)
    raw_val = 433
    norm_val = service.normalize_property_value("clay_percent", raw_val)
    assert norm_val == 43.3


# ==============================================================================
# 11. Successful Bulk Density Extraction Test
# ==============================================================================
def test_successful_bulk_density_extraction():
    service = SoilGridsService()
    # Raw bulk density bdod is in cg/cm³ -> convert to g/cm³ (divide by 100)
    raw_val = 160
    norm_val = service.normalize_property_value("bulk_density", raw_val)
    assert norm_val == 1.60


# ==============================================================================
# 12. Correct Scaling / Conversion Verification for All 7 Properties
# ==============================================================================
def test_all_properties_scaling():
    service = SoilGridsService()
    test_cases = {
        "ph": (65, 6.5),
        "nitrogen": (100, 1.0),
        "organic_carbon": (250, 25.0),
        "sand_percent": (400, 40.0),
        "silt_percent": (350, 35.0),
        "clay_percent": (250, 25.0),
        "bulk_density": (145, 1.45),
    }
    for prop, (raw, expected) in test_cases.items():
        assert service.normalize_property_value(prop, raw) == expected


# ==============================================================================
# 13. Missing Soil Value Becomes Null Test
# ==============================================================================
def test_missing_soil_value_becomes_null():
    service = SoilGridsService()
    # None raw value preserves null
    assert service.normalize_property_value("ph", None) is None
    assert service.normalize_property_value("nitrogen", None) is None
    assert service.normalize_property_value("organic_carbon", None) is None
    assert service.normalize_property_value("sand_percent", None) is None
    assert service.normalize_property_value("silt_percent", None) is None
    assert service.normalize_property_value("clay_percent", None) is None
    assert service.normalize_property_value("bulk_density", None) is None


# ==============================================================================
# 14. WCS Failure Handling Tests
# ==============================================================================
def test_wcs_timeout_error():
    mock_factory = MagicMock()
    mock_factory.side_effect = Exception("Read timed out")
    service = SoilGridsService(wcs_client_factory=mock_factory)

    with pytest.raises(SoilGridsTimeoutError):
        service.fetch_single_coverage_raw("ph", 0.0, 0.0)


def test_wcs_connection_error():
    mock_factory = MagicMock()
    mock_factory.side_effect = Exception("Connection refused")
    service = SoilGridsService(wcs_client_factory=mock_factory)

    with pytest.raises(SoilGridsConnectionError):
        service.fetch_single_coverage_raw("ph", 0.0, 0.0)


@patch("app.routes.environment.soilgrids_service.fetch_all_soil_properties")
def test_wcs_timeout_api(mock_fetch):
    mock_fetch.side_effect = SoilGridsTimeoutError("WCS timed out")
    response = client.get("/api/environment/soil?latitude=18.155&longitude=74.58")
    assert response.status_code == 504
    assert "timed out" in response.json()["detail"].lower()


@patch("app.routes.environment.soilgrids_service.fetch_all_soil_properties")
def test_wcs_failure_api(mock_fetch):
    mock_fetch.side_effect = SoilGridsConnectionError("WCS unavailable")
    response = client.get("/api/environment/soil?latitude=18.155&longitude=74.58")
    assert response.status_code == 502
    assert "Unable to retrieve soil data" in response.json()["detail"]


# ==============================================================================
# 15. Successful API Endpoint Response Test
# ==============================================================================
@patch("app.routes.environment.soilgrids_service.fetch_all_soil_properties")
def test_successful_soil_api_response(mock_fetch):
    mock_fetch.return_value = MOCK_NORMALIZED_SOIL

    response = client.get("/api/environment/soil?latitude=18.155&longitude=74.58")
    assert response.status_code == 200

    data = response.json()
    assert data["latitude"] == 18.155
    assert data["longitude"] == 74.58
    assert data["depth"] == "0-5cm"
    assert data["source"] == "ISRIC SoilGrids"
    assert "soil" in data

    soil = data["soil"]
    assert soil["ph"] == 7.2
    assert soil["nitrogen"] == 1.21
    assert soil["organic_carbon"] == 13.4
    assert soil["sand_percent"] == 32.6
    assert soil["silt_percent"] == 24.1
    assert soil["clay_percent"] == 43.3
    assert soil["bulk_density"] == 1.60
