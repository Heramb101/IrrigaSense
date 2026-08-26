import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.connection import Base, get_db
from app.models.models import User, Farm

from sqlalchemy.pool import StaticPool

import os
import tempfile

# Setup test DB
db_fd, db_path = tempfile.mkstemp()
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True, scope="session")
def cleanup_db():
    yield
    engine.dispose()
    try:
        os.close(db_fd)
    except OSError:
        pass
    try:
        os.unlink(db_path)
    except OSError:
        pass

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_farm():
    db = TestingSessionLocal()
    user = User(name="Test User", email="test@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)
    
    farm = Farm(owner_id=user.id, name="Test Farm", latitude=10.0, longitude=20.0, location_name="Test Loc")
    db.add(farm)
    db.commit()
    db.refresh(farm)
    yield farm
    db.close()

def valid_assessment_payload(farm_id):
    return {
        "farm_id": farm_id,
        "assessment_version": "1.0",
        "data": {
            "location": {
                "latitude": 10.0,
                "longitude": 20.0,
                "location_name": "",
                "location_confirmed": True
            },
            "farm": {
                "size_range": "1-2 acres",
                "experience_years_range": "3-5 years"
            },
            "land_history": {
                "previous_crops": [],
                "historical_problems": []
            },
            "soil": {
                "soilgrids": {
                    "ph": 6.0,
                    "nitrogen": 0.05
                },
                "farmer_report": {
                    "ph": 7.0
                },
                "soilgrids_confirmed": True,
                "has_soil_report": True,
                "observed_drainage": "Water drains normally"
            },
            "weather": {
                "farmer_confirmed": True
            },
            "crop": {
                "current_crop_id": "corn",
                "planting_date": "2023-01-01",
                "is_approximate_planting_date": False,
                "calculated_stage": "vegetative",
                "farmer_confirmed_stage": "vegetative",
                "health_condition": "healthy"
            },
            "irrigation": {
                "method": "drip",
                "water_source": "borewell",
                "water_reliability": "always",
                "current_frequency": "daily"
            },
            "farm_inputs": {},
            "goals": {}
        }
    }

# POST
def test_create_valid_assessment(test_farm):
    response = client.post("/api/assessments", json=valid_assessment_payload(test_farm.id))
    assert response.status_code == 201
    data = response.json()
    assert data["farm_id"] == test_farm.id
    # Test 4. Soil resolution was performed
    # Farmer pH takes precedence over SoilGrids pH
    assert data["data"]["soil"]["resolved"]["ph"] == 7.0
    # SoilGrids nitrogen maps to resolved n
    assert data["data"]["soil"]["resolved"]["n"] == 0.05

def test_reject_invalid_assessment(test_farm):
    payload = valid_assessment_payload(test_farm.id)
    del payload["data"]["location"] # missing required field
    response = client.post("/api/assessments", json=payload)
    assert response.status_code == 422

def test_nonexistent_farm_returns_404():
    response = client.post("/api/assessments", json=valid_assessment_payload(999))
    assert response.status_code == 404

# GET
def test_get_existing_assessment(test_farm):
    post_res = client.post("/api/assessments", json=valid_assessment_payload(test_farm.id))
    assessment_id = post_res.json()["id"]
    
    get_res = client.get(f"/api/assessments/{assessment_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == assessment_id

def test_nonexistent_assessment_returns_404():
    get_res = client.get("/api/assessments/999")
    assert get_res.status_code == 404

# PUT
def test_update_existing_assessment(test_farm):
    post_res = client.post("/api/assessments", json=valid_assessment_payload(test_farm.id))
    assessment_id = post_res.json()["id"]
    
    payload = {
        "assessment_version": "1.1",
        "data": valid_assessment_payload(test_farm.id)["data"]
    }
    # Modify data for PUT
    payload["data"]["soil"]["farmer_report"]["ph"] = 7.5
    
    put_res = client.put(f"/api/assessments/{assessment_id}", json=payload)
    assert put_res.status_code == 200
    data = put_res.json()
    assert data["assessment_version"] == "1.1"
    
    # Soil resolution runs again
    assert data["data"]["soil"]["resolved"]["ph"] == 7.5

def test_update_nonexistent_assessment():
    payload = {"assessment_version": "1.1"}
    put_res = client.put("/api/assessments/999", json=payload)
    assert put_res.status_code == 404
