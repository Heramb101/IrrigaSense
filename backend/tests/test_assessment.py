import pytest
from datetime import date
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base
from app.models.models import User, Farm, Assessment
from app.schemas.assessment import (
    AssessmentData, AssessmentCreate, SoilData, SoilGridsData, 
    FarmerSoilReport, LocationData, FarmDetails, LandHistory, 
    WeatherData, CropData, IrrigationData, FarmInputs, GoalsData
)
from app.services.soil_resolver import resolve_soil_values

# Setup DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)

def get_valid_assessment_data():
    return AssessmentData(
        location=LocationData(latitude=10.0, longitude=20.0, location_confirmed=True),
        farm=FarmDetails(size_range="1-2 acres", experience_years_range="3-5 years"),
        land_history=LandHistory(previous_crops=["wheat"], historical_problems=["drought"]),
        soil=SoilData(
            soilgrids_confirmed=True,
            has_soil_report=False,
            observed_drainage="Water drains normally"
        ),
        weather=WeatherData(farmer_confirmed=True),
        crop=CropData(
            current_crop_id="corn",
            planting_date=date(2023, 1, 1),
            is_approximate_planting_date=False,
            calculated_stage="vegetative",
            farmer_confirmed_stage="vegetative",
            health_condition="healthy"
        ),
        irrigation=IrrigationData(
            method="drip",
            water_source="borewell",
            water_reliability="always",
            current_frequency="daily"
        ),
        farm_inputs=FarmInputs(fertilizers=["urea"], pest_control=["none"]),
        goals=GoalsData(farmer_goals=["save water"])
    )

def test_create_valid_assessment(db):
    """Test 1 & 3: Creating a valid assessment & User -> Farm -> Assessment relationships"""
    user = User(name="Test User", email="test@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)
    
    farm = Farm(owner_id=user.id, name="Test Farm", latitude=10.0, longitude=20.0, location_name="Test Loc")
    db.add(farm)
    db.commit()
    db.refresh(farm)
    
    assessment_data = get_valid_assessment_data()
    create_schema = AssessmentCreate(farm_id=farm.id, data=assessment_data)
    
    assessment = Assessment(
        farm_id=create_schema.farm_id,
        assessment_version=create_schema.assessment_version,
        data=create_schema.data.model_dump(mode='json')
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    # Assert Relationships
    assert assessment.id is not None
    assert assessment.farm.id == farm.id
    assert assessment.farm.owner.id == user.id
    
    # Verify data format in DB
    assert assessment.data["location"]["latitude"] == 10.0
    assert assessment.data["soil"]["observed_drainage"] == "Water drains normally"

def test_reject_invalid_assessment_data():
    """Test 2: Rejecting invalid assessment data"""
    invalid_data = {
        "location": {"latitude": "not a float"} # Missing required fields
    }
    with pytest.raises(ValidationError):
        AssessmentData(**invalid_data)

def test_soil_precedence_logic():
    """Test 4: Soil precedence/resolution logic using mock values"""
    soil = SoilData(
        soilgrids=SoilGridsData(ph=5.5, clay=30.0, sand=40.0, nitrogen=0.1),
        farmer_report=FarmerSoilReport(ph=6.5, n=100.0), # Farmer report pH/n should take precedence
        soilgrids_confirmed=True,
        has_soil_report=True,
        observed_drainage="normally"
    )
    resolved_soil = resolve_soil_values(soil)
    
    assert resolved_soil.resolved.ph == 6.5
    assert resolved_soil.source["ph"] == "farmer_report"
    
    assert resolved_soil.resolved.n == 100.0
    assert resolved_soil.source["n"] == "farmer_report"
    
    assert resolved_soil.resolved.clay == 30.0
    assert resolved_soil.source["clay"] == "soilgrids"
    
    assert resolved_soil.resolved.organic_carbon is None
    assert resolved_soil.source["organic_carbon"] is None

def test_missing_soilgrids_values():
    """Test 5: Handling missing SoilGrids values."""
    soil = SoilData(
        soilgrids=None,
        farmer_report=FarmerSoilReport(ph=7.0),
        soilgrids_confirmed=False,
        has_soil_report=True,
        observed_drainage="normally"
    )
    resolved_soil = resolve_soil_values(soil)
    assert resolved_soil.resolved.ph == 7.0
    assert resolved_soil.resolved.clay is None
    assert resolved_soil.source["ph"] == "farmer_report"
    assert resolved_soil.source["clay"] is None

def test_missing_farmer_soil_report_values():
    """Test 6: Handling missing farmer soil-report values."""
    soil = SoilData(
        soilgrids=SoilGridsData(ph=6.0, sand=50.0, nitrogen=0.05),
        farmer_report=None,
        soilgrids_confirmed=True,
        has_soil_report=False,
        observed_drainage="normally"
    )
    resolved_soil = resolve_soil_values(soil)
    assert resolved_soil.resolved.ph == 6.0
    assert resolved_soil.resolved.sand == 50.0
    assert resolved_soil.resolved.n == 0.05
    assert resolved_soil.source["ph"] == "soilgrids"
    assert resolved_soil.source["n"] == "soilgrids"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
