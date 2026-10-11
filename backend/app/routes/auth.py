from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from typing import Optional, Tuple

from app.database.connection import get_db
from app.models.models import User, UserSession
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserRead,
    AuthResponse,
    MessageResponse,
)
from app.services import auth_service
from app.config import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    SECURE_COOKIES,
    SESSION_COOKIE_SAMESITE,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

def get_session_token_from_request(request: Request) -> Optional[str]:
    """Extracts session token from HttpOnly cookie, Authorization header, or custom header."""
    # 1. Cookie
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        return token

    # 2. Authorization header (Bearer <token>)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    # 3. Direct Session Token Header
    custom_header = request.headers.get("X-Session-Token")
    if custom_header:
        return custom_header.strip()

    return None

def get_current_user_and_session(
    request: Request, db: Session = Depends(get_db)
) -> Tuple[User, UserSession]:
    """Strict dependency requiring an active, unexpired session."""
    raw_token = get_session_token_from_request(request)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user, session = auth_service.get_user_and_session_by_token(db, raw_token)
    if not user or not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid or has expired",
        )

    return user, session

def get_current_user(
    user_and_session: Tuple[User, UserSession] = Depends(get_current_user_and_session)
) -> User:
    """Convenience dependency to get the current authenticated User."""
    return user_and_session[0]

def get_optional_current_user(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    """Optional dependency that returns User if authenticated or None if anonymous."""
    raw_token = get_session_token_from_request(request)
    if not raw_token:
        return None

    user, _ = auth_service.get_user_and_session_by_token(db, raw_token)
    return user

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    req: UserRegisterRequest,
    response: Response,
    db: Session = Depends(get_db)
) -> AuthResponse:
    """Registers a new user account with Argon2id password hashing and logs them in."""
    try:
        normalized_username = auth_service.validate_username(req.username)
        auth_service.validate_password(req.password)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )

    # Check for duplicate username
    existing_user = db.query(User).filter(User.username == normalized_username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken",
        )

    # Create user with Argon2id hash
    ph = auth_service.hash_password(req.password)
    new_user = User(
        username=normalized_username,
        password_hash=ph,
        name=req.name.strip() if req.name else normalized_username,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create session and deliver via HttpOnly cookie
    session, raw_token, csrf_token = auth_service.create_user_session(db, new_user.id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite=SESSION_COOKIE_SAMESITE,
        secure=SECURE_COOKIES,
        path="/",
    )

    return AuthResponse(
        user=UserRead.model_validate(new_user),
        message="Account registered successfully",
        csrf_token=csrf_token,
    )

@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
def login_user(
    req: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db)
) -> AuthResponse:
    """Authenticates a user by username and password, delivering an HttpOnly session cookie."""
    normalized_username = auth_service.normalize_username(req.username)
    user = db.query(User).filter(User.username == normalized_username).first()

    # Verify password safely using Argon2id
    is_valid = auth_service.verify_password(req.password, user.password_hash if user else None)
    if not user or not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Create session and set cookie
    session, raw_token, csrf_token = auth_service.create_user_session(db, user.id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite=SESSION_COOKIE_SAMESITE,
        secure=SECURE_COOKIES,
        path="/",
    )

    return AuthResponse(
        user=UserRead.model_validate(user),
        message="Login successful",
        csrf_token=csrf_token,
    )

@router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def logout_user(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
) -> MessageResponse:
    """Invalidates the server session and removes the session cookie."""
    raw_token = get_session_token_from_request(request)
    if raw_token:
        auth_service.invalidate_session_token(db, raw_token)

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
    )
    return MessageResponse(message="Successfully logged out")

@router.get("/me", response_model=AuthResponse, status_code=status.HTTP_200_OK)
def get_current_user_profile(
    user_and_session: Tuple[User, UserSession] = Depends(get_current_user_and_session)
) -> AuthResponse:
    """Returns the profile and current CSRF token of the authenticated user."""
    user, session = user_and_session
    return AuthResponse(
        user=UserRead.model_validate(user),
        message="Authenticated",
        csrf_token=session.csrf_token,
    )
