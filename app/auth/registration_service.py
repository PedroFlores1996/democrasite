from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import User, PendingRegistration
from app.schemas import UserCreate
from app.services.email_service import (
    email_service, 
    generate_verification_token, 
    get_token_expiration
)
# Import password hashing directly to avoid circular imports
from passlib.context import CryptContext

# Import cleanup function
from app.auth.cleanup_service import cleanup_expired_pending_registrations

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def check_existing_user(db: Session, username: str, email: str):
    """Check if username or email already exists in active users."""
    existing_user = db.query(User).filter(
        (User.username == username.lower()) | (User.email == email)
    ).first()
    
    if existing_user:
        if existing_user.username == username.lower():
            raise HTTPException(status_code=400, detail="Username already registered")
        else:
            raise HTTPException(status_code=400, detail="Email already registered")


def create_development_user(db: Session, user: UserCreate) -> dict:
    """Create user immediately for development mode (no email verification)."""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username.lower(),
        email=user.email,
        hashed_password=hashed_password
        # Note: With staged registration, all users in DB are verified by definition
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {
        "message": "Registration successful! You can now log in.",
        "email_sent": False,
        "username": user.username,
        "requires_verification": False
    }


def create_production_pending_user(db: Session, user: UserCreate) -> dict:
    """Create pending registration for production mode (with email verification)."""
    # TODO: Optimize pending registration cleanup strategy
    # Current: Clean up ALL expired registrations on every registration call
    # Alternative approaches to consider:
    # 1. Background job: Run cleanup on scheduled basis (e.g., hourly via cron/celery)
    # 2. Lazy cleanup: Only clean expired records for specific email being registered
    # 3. Batch cleanup: Run full cleanup every N registrations or after X minutes
    # 4. Database-level: Use PostgreSQL TTL with triggers or pg_cron extension
    #    - CREATE TRIGGER on INSERT to cleanup expired rows
    #    - SELECT cron.schedule() for periodic cleanup without app involvement
    # 5. Partition tables: Auto-drop old partitions based on expiration dates
    # Current approach trades some registration latency for data consistency
    cleanup_expired_pending_registrations(db)
    
    # Clean up any existing pending registrations for this email/username
    db.query(PendingRegistration).filter(
        (PendingRegistration.username == user.username.lower()) | 
        (PendingRegistration.email == user.email)
    ).delete(synchronize_session=False)
    
    verification_token = generate_verification_token()
    token_expires = get_token_expiration()
    hashed_password = get_password_hash(user.password)
    
    # Create pending registration (not actual user yet)
    pending_registration = PendingRegistration(
        username=user.username.lower(),
        email=user.email,
        hashed_password=hashed_password,
        verification_token=verification_token,
        verification_token_expires=token_expires
    )
    db.add(pending_registration)
    db.commit()
    db.refresh(pending_registration)
    
    # Send verification email
    email_sent = email_service.send_verification_email(
        to_email=user.email,
        username=user.username,
        verification_token=verification_token
    )
    
    if not email_sent:
        # If email fails, clean up the pending registration
        db.delete(pending_registration)
        db.commit()
        raise HTTPException(
            status_code=500, 
            detail="Failed to send verification email. Please try again."
        )
    
    return {
        "message": "Registration successful! Please check your email to verify your account before logging in.",
        "email_sent": True,
        "username": user.username,
        "requires_verification": True
    }