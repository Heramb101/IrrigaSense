import secrets
import hashlib
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from sqlalchemy.orm import Session

from app.models.models import User, UserSession, utc_now
from app.config import (
    SESSION_MAX_AGE_SECONDS,
    MIN_USERNAME_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH,
    MAX_PASSWORD_LENGTH,
)

# Argon2id password hasher with secure, robust defaults
_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
)

def hash_password(password: str) -> str:
    """Hashes a plaintext password using Argon2id."""
    return _password_hasher.hash(password)

def verify_password(password: str, password_hash: Optional[str]) -> bool:
    """Verifies a plaintext password against an Argon2id hash safely."""
    if not password or not password_hash:
        return False
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False

def normalize_username(username: str) -> str:
    """Normalizes a username (lowercased and stripped)."""
    if not username:
        return ""
    return username.strip().lower()

def validate_username(username: str) -> str:
    """Validates and returns normalized username or raises ValueError."""
    if not username:
        raise ValueError("Username is required")
    normalized = normalize_username(username)
    if len(normalized) < MIN_USERNAME_LENGTH or len(normalized) > MAX_USERNAME_LENGTH:
        raise ValueError(
            f"Username must be between {MIN_USERNAME_LENGTH} and {MAX_USERNAME_LENGTH} characters"
        )
    if not re.match(r"^[a-z0-9_]+$", normalized):
        raise ValueError("Username may only contain lowercase letters, numbers, and underscores")
    return normalized

def validate_password(password: str) -> None:
    """Validates plaintext password constraints."""
    if not password:
        raise ValueError("Password is required")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password must not exceed {MAX_PASSWORD_LENGTH} characters")

def generate_session_token() -> str:
    """Generates a cryptographically strong unpredictable session token."""
    return secrets.token_urlsafe(32)

def hash_session_token(token: str) -> str:
    """Generates SHA-256 digest of session token for server storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def generate_csrf_token() -> str:
    """Generates a secure CSRF token."""
    return secrets.token_urlsafe(32)

def create_user_session(db: Session, user_id: int) -> Tuple[UserSession, str, str]:
    """Creates a persistent server session record, returning (session, raw_token, csrf_token)."""
    raw_token = generate_session_token()
    token_hash = hash_session_token(raw_token)
    csrf_token = generate_csrf_token()
    expires_at = utc_now() + timedelta(seconds=SESSION_MAX_AGE_SECONDS)

    session = UserSession(
        user_id=user_id,
        token_hash=token_hash,
        csrf_token=csrf_token,
        expires_at=expires_at,
        last_used_at=utc_now(),
        is_active=True,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session, raw_token, csrf_token

def get_user_and_session_by_token(
    db: Session, raw_token: Optional[str]
) -> Tuple[Optional[User], Optional[UserSession]]:
    """Looks up active, unexpired session by raw token and updates last_used_at."""
    if not raw_token:
        return None, None
    token_hash = hash_session_token(raw_token.strip())
    now = utc_now()

    session = (
        db.query(UserSession)
        .filter(
            UserSession.token_hash == token_hash,
            UserSession.is_active == True,
            UserSession.expires_at > now,
        )
        .first()
    )
    if not session:
        return None, None

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        return None, None

    session.last_used_at = now
    db.commit()
    return user, session

def invalidate_session_token(db: Session, raw_token: Optional[str]) -> bool:
    """Marks a session as inactive."""
    if not raw_token:
        return False
    token_hash = hash_session_token(raw_token.strip())
    session = db.query(UserSession).filter(UserSession.token_hash == token_hash).first()
    if session:
        session.is_active = False
        db.commit()
        return True
    return False
