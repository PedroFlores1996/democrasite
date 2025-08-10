from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.schemas import UserCreate, UserLogin, Token, UserStats
from app.auth.utils import (
    verify_password, 
    create_access_token,
    get_current_user,
    check_existing_user,
    create_development_user,
    create_production_pending_user,
    cleanup_expired_pending_registrations,
    verify_pending_registration,
    resend_verification_to_pending_user,
    delete_user_data
)
from app.config.settings import settings
from app.db.database import get_db
from app.db.models import User, Topic, Vote

router = APIRouter()

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists in active users
    check_existing_user(db, user.username, user.email)
    
    # Conditional email verification based on environment
    if settings.REQUIRE_EMAIL_VERIFICATION:
        # Production mode - use staged registration with pending verification
        return create_production_pending_user(db, user)
    else:
        # Development mode - create user immediately (old behavior)
        return create_development_user(db, user)

@router.post("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user's email address using the verification token"""
    if not settings.REQUIRE_EMAIL_VERIFICATION:
        raise HTTPException(
            status_code=400, 
            detail="Email verification is disabled in development mode"
        )
    
    # Production mode - verify pending registration
    result = verify_pending_registration(db, token)
    if result is not None:
        return result
    
    # No pending registration found - invalid token
    raise HTTPException(status_code=400, detail="Invalid or expired verification token")

@router.post("/resend-verification")
def resend_verification_email(email: str, db: Session = Depends(get_db)):
    """Resend verification email to user"""
    if not settings.REQUIRE_EMAIL_VERIFICATION:
        raise HTTPException(
            status_code=400, 
            detail="Email verification is disabled in development mode"
        )
    
    # Production mode - resend to pending registration
    result = resend_verification_to_pending_user(db, email)
    if result is not None:
        return result
    
    # No pending registration found
    return {"message": "If the email exists, a verification email has been sent"}

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username.lower()).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Note: With staged registration, all users in the database are verified by definition
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username.lower()}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
def token_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 compatible login endpoint for Swagger UI"""
    db_user = db.query(User).filter(User.username == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Note: With staged registration, all users in the database are verified by definition
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return {
        "username": current_user.username, 
        "id": current_user.id,
        "email": current_user.email
        # Note: email_verified field removed - with staged registration, all users are verified by definition
    }


@router.get("/users/me/stats", response_model=UserStats)
def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's statistics for profile page"""
    # Count topics created by user
    topics_created = db.query(Topic).filter(Topic.created_by == current_user.id).count()
    
    # Count votes cast by user
    votes_cast = db.query(Vote).filter(Vote.user_id == current_user.id).count()
    
    # Count favorite topics (using relationship)
    db.refresh(current_user)  # Ensure we have fresh relationship data
    favorite_topics = len(current_user.favorite_topics)
    
    return UserStats(
        username=current_user.username,
        user_id=current_user.id,
        created_at=current_user.created_at,
        topics_created=topics_created,
        votes_cast=votes_cast,
        favorite_topics=favorite_topics
    )


@router.delete("/users/me")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current user's account and all associated data"""
    return delete_user_data(db, current_user)


@router.post("/cleanup-expired-registrations")
def cleanup_expired_registrations_endpoint(db: Session = Depends(get_db)):
    """Manual cleanup endpoint for expired pending registrations (admin use)"""
    count = cleanup_expired_pending_registrations(db)
    return {
        "message": f"Cleaned up {count} expired pending registrations",
        "cleaned_up": count
    }