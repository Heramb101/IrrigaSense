import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./irrigasense.db")

# Authentication and Sessions
SESSION_SECRET = os.getenv("SESSION_SECRET", "irrigasense_dev_secret_key_change_in_production")
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "irrigasense_session")
SESSION_MAX_AGE_SECONDS = int(os.getenv("SESSION_MAX_AGE_SECONDS", str(30 * 24 * 3600)))  # 30 days
SECURE_COOKIES = os.getenv("SECURE_COOKIES", "false").lower() in ("true", "1")
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "lax")

# Username & Password validation rules
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 30
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# CORS Configuration
raw_cors = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
)
CORS_ORIGINS = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]
