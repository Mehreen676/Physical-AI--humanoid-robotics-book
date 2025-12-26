"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)
from app.models.user import User, UserPreferences
from app.schemas.auth import (
    SignupRequest,
    SigninRequest,
    TokenResponse,
    UserProfile,
    UserUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=TokenResponse)
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    User signup endpoint.

    Creates new user account and returns JWT token.
    """
    # Check if user exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        logger.warning(f"Signup attempt with existing email: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    try:
        new_user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            background_software=request.background_software,
            background_hardware=request.background_hardware,
            learning_goal=request.learning_goal,
        )
        db.add(new_user)
        db.flush()

        # Create user preferences
        preferences = UserPreferences(user_id=new_user.id)
        db.add(preferences)

        db.commit()
        logger.info(f"New user created: {new_user.email}")

        # Create token
        access_token = create_access_token(
            data={"sub": new_user.id, "email": new_user.email}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 30 * 24 * 60 * 60,  # 30 days in seconds
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account",
        )


@router.post("/signin", response_model=TokenResponse)
async def signin(
    request: SigninRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    User signin endpoint.

    Authenticates user and returns JWT token.
    """
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        logger.warning(f"Failed signin attempt: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Create token
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email}
    )

    logger.info(f"User signin: {user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 30 * 24 * 60 * 60,  # 30 days in seconds
    }


@router.post("/logout")
async def logout(credentials: HTTPAuthCredentials = Depends(security)) -> dict:
    """
    User logout endpoint.

    Invalidates token (client should discard it).
    """
    logger.info("User logout")
    return {"status": "success", "message": "Logged out successfully"}


@router.get("/me", response_model=UserProfile)
async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user profile.

    Requires valid JWT token.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.put("/me", response_model=UserProfile)
async def update_current_user(
    request: UserUpdate,
    credentials: HTTPAuthCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Update current user profile.

    Requires valid JWT token.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update fields
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    logger.info(f"User profile updated: {user.email}")

    return user
