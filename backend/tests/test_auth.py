import os
import tempfile
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.connection import Base, get_db
from app.models.models import User, Farm, Assessment, UserSession, utc_now
from app.services import auth_service
from app.config import SESSION_COOKIE_NAME

# Isolated Test Database Setup
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
    client.cookies.clear()
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    client.cookies.clear()
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def test_user_and_farm():
    db = TestingSessionLocal()
    # Create user with argon2 hash
    ph = auth_service.hash_password("password123")
    user = User(username="farmer_ramesh", password_hash=ph, name="Ramesh Patel")
    db.add(user)
    db.commit()
    db.refresh(user)

    farm = Farm(
        owner_id=user.id,
        name="Ramesh Farm",
        latitude=18.1519,
        longitude=74.5770,
        location_name="Baramati, Maharashtra"
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    yield user, farm
    db.close()

def valid_assessment_payload(farm_id: int):
    return {
        "farm_id": farm_id,
        "assessment_version": "2.0",
        "data": {
            "location": {
                "latitude": 18.1519,
                "longitude": 74.5770,
                "location_name": "Baramati, Maharashtra",
                "location_confirmed": True
            },
            "farm": {
                "size_range": "2–5 acres",
                "experience_years_range": "5-10 years"
            },
            "land_history": {
                "previous_crops": ["Sugarcane"],
                "historical_problems": []
            },
            "soil": {
                "soilgrids": {
                    "ph": 6.8,
                    "nitrogen": 0.08
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
                "current_crop_id": "sugarcane",
                "planting_date": "2026-08-15",
                "is_approximate_planting_date": False,
                "calculated_stage": "vegetative",
                "farmer_confirmed_stage": "vegetative",
                "health_condition": "healthy"
            },
            "irrigation": {
                "method": "drip",
                "water_source": "canal",
                "water_reliability": "always",
                "current_frequency": "alternate_days"
            },
            "farm_inputs": {
                "fertilizers": ["urea", "dap"]
            },
            "goals": {
                "farmer_goals": ["yield_maximization"]
            }
        }
    }


# ==============================================================================
# 1. USER REGISTRATION TESTS
# ==============================================================================

def test_register_success():
    """Test successful user registration creates Argon2id hash and delivers HttpOnly cookie."""
    res = client.post(
        "/api/auth/register",
        json={
            "username": "farmer_kavita",
            "password": "SecurePassword123!",
            "name": "Kavita Sharma"
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["username"] == "farmer_kavita"
    assert data["user"]["name"] == "Kavita Sharma"
    assert "csrf_token" in data
    assert SESSION_COOKIE_NAME in res.cookies

    # Verify password hash stored in DB is Argon2id
    db = TestingSessionLocal()
    user = db.query(User).filter(User.username == "farmer_kavita").first()
    assert user is not None
    assert user.password_hash.startswith("$argon2id$")
    assert auth_service.verify_password("SecurePassword123!", user.password_hash)
    db.close()

def test_register_duplicate_username_rejected(test_user_and_farm):
    """Test registering an existing username returns 400."""
    res = client.post(
        "/api/auth/register",
        json={
            "username": "farmer_ramesh",  # Already exists
            "password": "NewPassword123!",
            "name": "Another Ramesh"
        }
    )
    assert res.status_code == 400
    assert "already taken" in res.json()["detail"].lower()

def test_register_invalid_username():
    """Test invalid username formats are rejected."""
    # Too short
    res = client.post("/api/auth/register", json={"username": "ab", "password": "ValidPassword123!"})
    assert res.status_code in (400, 422)

    # Invalid characters (spaces, special symbols)
    res = client.post("/api/auth/register", json={"username": "farmer ram!", "password": "ValidPassword123!"})
    assert res.status_code in (400, 422)

def test_register_short_password():
    """Test passwords under minimum length are rejected."""
    res = client.post("/api/auth/register", json={"username": "valid_user", "password": "123"})
    assert res.status_code == 422 or res.status_code == 400


# ==============================================================================
# 2. LOGIN & AUTHENTICATION TESTS
# ==============================================================================

def test_login_success(test_user_and_farm):
    """Test login with valid credentials delivers HttpOnly session cookie."""
    res = client.post(
        "/api/auth/login",
        json={
            "username": "farmer_ramesh",
            "password": "password123"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["username"] == "farmer_ramesh"
    assert "csrf_token" in data
    assert SESSION_COOKIE_NAME in res.cookies

def test_login_invalid_password(test_user_and_farm):
    """Test login with wrong password returns generic 401."""
    res = client.post(
        "/api/auth/login",
        json={
            "username": "farmer_ramesh",
            "password": "wrongpassword"
        }
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid username or password"

def test_login_nonexistent_username():
    """Test login with unknown username returns same generic 401."""
    res = client.post(
        "/api/auth/login",
        json={
            "username": "nonexistent_farmer",
            "password": "somepassword"
        }
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid username or password"

def test_get_me_authenticated(test_user_and_farm):
    """Test /api/auth/me returns authenticated user profile."""
    # Log in
    login_res = client.post(
        "/api/auth/login",
        json={"username": "farmer_ramesh", "password": "password123"}
    )
    assert login_res.status_code == 200

    # Request /me with session cookie
    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["user"]["username"] == "farmer_ramesh"
    assert data["user"]["name"] == "Ramesh Patel"
    assert "csrf_token" in data

def test_get_me_unauthenticated():
    """Test /api/auth/me without session cookie returns 401."""
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]

def test_logout(test_user_and_farm):
    """Test logout invalidates session on server and clears cookie."""
    # Log in
    login_res = client.post(
        "/api/auth/login",
        json={"username": "farmer_ramesh", "password": "password123"}
    )
    assert login_res.status_code == 200

    # Logout
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Successfully logged out"

    # Subsequent /me request should be unauthorized
    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 401

def test_expired_session_rejected(test_user_and_farm):
    """Test expired session token is rejected with 401."""
    user, _ = test_user_and_farm
    db = TestingSessionLocal()
    # Create expired session
    session, raw_token, _ = auth_service.create_user_session(db, user.id)
    session.expires_at = utc_now() - timedelta(hours=1)
    db.commit()
    db.close()

    # Call with expired token header
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {raw_token}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower() or "required" in res.json()["detail"].lower()


# ==============================================================================
# 3. ASSESSMENT OWNERSHIP & ACCESS CONTROL TESTS
# ==============================================================================

def test_authenticated_assessment_creation_associates_owner(test_user_and_farm):
    """Test creating an assessment while logged in attaches current user_id."""
    user, farm = test_user_and_farm

    # Log in as Ramesh
    login_res = client.post(
        "/api/auth/login",
        json={"username": "farmer_ramesh", "password": "password123"}
    )
    assert login_res.status_code == 200

    # Post assessment
    post_res = client.post("/api/assessments", json=valid_assessment_payload(farm.id))
    assert post_res.status_code == 201
    data = post_res.json()
    assert data["user_id"] == user.id

    # Verify in DB
    db = TestingSessionLocal()
    saved = db.query(Assessment).filter(Assessment.id == data["id"]).first()
    assert saved.user_id == user.id
    db.close()

def test_get_my_assessments_lists_only_current_user_records(test_user_and_farm):
    """Test /api/assessments/mine lists only the authenticated user's records, newest first."""
    user1, farm1 = test_user_and_farm

    # Create second user & farm
    db = TestingSessionLocal()
    ph = auth_service.hash_password("password456")
    user2 = User(username="farmer_suresh", password_hash=ph, name="Suresh Patil")
    db.add(user2)
    db.commit()
    db.refresh(user2)
    farm2 = Farm(owner_id=user2.id, name="Suresh Farm", latitude=19.99, longitude=73.78)
    db.add(farm2)
    db.commit()
    db.refresh(farm2)
    db.close()

    # 1. Login as Ramesh and create 2 assessments
    client.post("/api/auth/login", json={"username": "farmer_ramesh", "password": "password123"})
    r1 = client.post("/api/assessments", json=valid_assessment_payload(farm1.id)).json()
    r2 = client.post("/api/assessments", json=valid_assessment_payload(farm1.id)).json()

    # 2. Login as Suresh and create 1 assessment
    client.post("/api/auth/login", json={"username": "farmer_suresh", "password": "password456"})
    s1 = client.post("/api/assessments", json=valid_assessment_payload(farm2.id)).json()

    # 3. Suresh calls /api/assessments/mine
    mine_suresh = client.get("/api/assessments/mine")
    assert mine_suresh.status_code == 200
    suresh_list = mine_suresh.json()
    assert len(suresh_list) == 1
    assert suresh_list[0]["id"] == s1["id"]

    # 4. Ramesh calls /api/assessments/mine
    client.post("/api/auth/login", json={"username": "farmer_ramesh", "password": "password123"})
    mine_ramesh = client.get("/api/assessments/mine")
    assert mine_ramesh.status_code == 200
    ramesh_list = mine_ramesh.json()
    assert len(ramesh_list) == 2
    ids = [a["id"] for a in ramesh_list]
    assert r1["id"] in ids
    assert r2["id"] in ids
    assert s1["id"] not in ids

def test_cross_user_assessment_access_denied(test_user_and_farm):
    """Test User A cannot view or update User B's assessment (403 Forbidden)."""
    user1, farm1 = test_user_and_farm

    # Create User 2
    db = TestingSessionLocal()
    ph = auth_service.hash_password("password456")
    user2 = User(username="farmer_suresh", password_hash=ph, name="Suresh Patil")
    db.add(user2)
    db.commit()
    db.refresh(user2)
    db.close()

    # Ramesh logs in and creates an assessment
    client.post("/api/auth/login", json={"username": "farmer_ramesh", "password": "password123"})
    ramesh_asmt = client.post("/api/assessments", json=valid_assessment_payload(farm1.id)).json()
    asmt_id = ramesh_asmt["id"]

    # Suresh logs in
    client.post("/api/auth/login", json={"username": "farmer_suresh", "password": "password456"})

    # Suresh tries to GET Ramesh's assessment -> 403 Forbidden
    get_res = client.get(f"/api/assessments/{asmt_id}")
    assert get_res.status_code == 403
    assert "access denied" in get_res.json()["detail"].lower()

    # Suresh tries to PUT Ramesh's assessment -> 403 Forbidden
    put_res = client.put(f"/api/assessments/{asmt_id}", json={"assessment_version": "9.9"})
    assert put_res.status_code == 403
    assert "access denied" in put_res.json()["detail"].lower()

def test_unauthenticated_cannot_access_owned_assessment(test_user_and_farm):
    """Test anonymous user cannot view owned assessment."""
    user1, farm1 = test_user_and_farm
    client.post("/api/auth/login", json={"username": "farmer_ramesh", "password": "password123"})
    ramesh_asmt = client.post("/api/assessments", json=valid_assessment_payload(farm1.id)).json()
    asmt_id = ramesh_asmt["id"]

    # Log out
    client.post("/api/auth/logout")

    # Anonymous GET -> 403 Forbidden
    get_res = client.get(f"/api/assessments/{asmt_id}")
    assert get_res.status_code == 403

def test_legacy_unowned_assessment_handling(test_user_and_farm):
    """Test legacy assessments created without owner (user_id=None) are retrievable."""
    _, farm = test_user_and_farm

    # Ensure unauthenticated
    client.post("/api/auth/logout")

    # Create unowned assessment
    post_res = client.post("/api/assessments", json=valid_assessment_payload(farm.id))
    assert post_res.status_code == 201
    asmt_id = post_res.json()["id"]
    assert post_res.json()["user_id"] is None

    # Retrieve unowned assessment anonymously
    get_res = client.get(f"/api/assessments/{asmt_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == asmt_id

def test_get_mine_requires_authentication():
    """Test calling /api/assessments/mine without auth returns 401."""
    client.post("/api/auth/logout")
    res = client.get("/api/assessments/mine")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]
