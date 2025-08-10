from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone

from app.schemas import UserCreate, UserLogin, Token, UserStats
from app.auth.utils import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    get_current_user
)
from app.config.settings import settings
from app.db.database import get_db
from app.db.models import User, Topic, Vote, PendingRegistration
from app.services.email_service import (
    email_service, 
    generate_verification_token, 
    get_token_expiration, 
    is_token_expired
)

router = APIRouter()

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists in active users
    existing_user = db.query(User).filter(
        (User.username == user.username.lower()) | (User.email == user.email)
    ).first()
    
    if existing_user:
        if existing_user.username == user.username.lower():
            raise HTTPException(status_code=400, detail="Username already registered")
        else:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Conditional email verification based on environment
    if settings.REQUIRE_EMAIL_VERIFICATION:
        # Production mode - use staged registration with pending verification
        
        # Clean up expired pending registrations periodically
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
    else:
        # Development mode - create user immediately (old behavior)
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username.lower(),
            email=user.email,
            hashed_password=hashed_password,
            email_verified=True,
            verification_token=None,
            verification_token_expires=None
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

@router.post("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user's email address using the verification token"""
    if settings.REQUIRE_EMAIL_VERIFICATION:
        # Production mode - look for pending registration first
        pending_registration = db.query(PendingRegistration).filter(
            PendingRegistration.verification_token == token
        ).first()
        
        if pending_registration:
            # Found pending registration - verify and create actual user
            if is_token_expired(pending_registration.verification_token_expires):
                # Clean up expired pending registration
                db.delete(pending_registration)
                db.commit()
                raise HTTPException(status_code=400, detail="Verification token has expired")
            
            # Check if user was created in the meantime (race condition protection)
            existing_user = db.query(User).filter(
                (User.username == pending_registration.username) | (User.email == pending_registration.email)
            ).first()
            
            if existing_user:
                # Clean up pending registration since user already exists
                db.delete(pending_registration)
                db.commit()
                raise HTTPException(status_code=400, detail="User already registered")
            
            # Create actual user from pending registration
            db_user = User(
                username=pending_registration.username,
                email=pending_registration.email,
                hashed_password=pending_registration.hashed_password,
                email_verified=True,
                verification_token=None,
                verification_token_expires=None
            )
            db.add(db_user)
            
            # Clean up the pending registration
            db.delete(pending_registration)
            db.commit()
            db.refresh(db_user)
            
            return {"message": "Email verified successfully! You can now log in."}
    
    # Fall back to old verification system (for development mode or legacy users)
    user = db.query(User).filter(User.verification_token == token).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    
    if user.email_verified:
        return {"message": "Email already verified"}
    
    if is_token_expired(user.verification_token_expires):
        raise HTTPException(status_code=400, detail="Verification token has expired")
    
    # Mark email as verified and clear verification token
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()
    
    return {"message": "Email verified successfully! You can now log in."}

@router.post("/resend-verification")
def resend_verification_email(email: str, db: Session = Depends(get_db)):
    """Resend verification email to user"""
    if settings.REQUIRE_EMAIL_VERIFICATION:
        # Production mode - check pending registrations first
        pending_registration = db.query(PendingRegistration).filter(
            PendingRegistration.email == email
        ).first()
        
        if pending_registration:
            # Generate new verification token for pending registration
            verification_token = generate_verification_token()
            token_expires = get_token_expiration()
            
            pending_registration.verification_token = verification_token
            pending_registration.verification_token_expires = token_expires
            db.commit()
            
            # Send verification email
            email_sent = email_service.send_verification_email(
                to_email=pending_registration.email,
                username=pending_registration.username,
                verification_token=verification_token
            )
            
            if not email_sent:
                raise HTTPException(status_code=500, detail="Failed to send verification email")
            
            return {"message": "Verification email sent"}
    
    # Fall back to old system for existing users or development mode
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a verification email has been sent"}
    
    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Generate new verification token
    verification_token = generate_verification_token()
    token_expires = get_token_expiration()
    
    user.verification_token = verification_token
    user.verification_token_expires = token_expires
    db.commit()
    
    # Send verification email
    email_sent = email_service.send_verification_email(
        to_email=user.email,
        username=user.username,
        verification_token=verification_token
    )
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send verification email")
    
    return {"message": "Verification email sent"}

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username.lower()).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if email is verified (only in production mode)
    if settings.REQUIRE_EMAIL_VERIFICATION and not db_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email address before logging in",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
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
    
    # Check if email is verified (only in production mode)
    if settings.REQUIRE_EMAIL_VERIFICATION and not db_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email address before logging in",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
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
        "email": current_user.email,
        "email_verified": current_user.email_verified
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
    # Delete user's votes
    user_votes = db.query(Vote).filter(Vote.user_id == current_user.id).all()
    votes_deleted = len(user_votes)
    for vote in user_votes:
        db.delete(vote)
    
    # Delete user's topics (this will cascade to related votes and access records)
    user_topics = db.query(Topic).filter(Topic.created_by == current_user.id).all()
    topics_deleted = len(user_topics)
    for topic in user_topics:
        # Delete all votes for this topic
        topic_votes = db.query(Vote).filter(Vote.topic_id == topic.id).all()
        for vote in topic_votes:
            db.delete(vote)
        db.delete(topic)
    
    # Remove user from favorites relationships (SQLAlchemy will handle the association table)
    current_user.favorite_topics.clear()
    
    # Delete the user
    db.delete(current_user)
    db.commit()
    
    return {
        "message": "Account deleted successfully",
        "topics_deleted": topics_deleted,
        "votes_deleted": votes_deleted
    }

def cleanup_expired_pending_registrations(db: Session) -> int:
    """Clean up expired pending registrations. Returns number of records cleaned up."""
    current_time = datetime.now(timezone.utc)
    
    # Delete all expired pending registrations
    expired_registrations = db.query(PendingRegistration).filter(
        PendingRegistration.verification_token_expires < current_time
    )
    
    count = expired_registrations.count()
    expired_registrations.delete(synchronize_session=False)
    db.commit()
    
    return count

@router.post("/cleanup-expired-registrations")
def cleanup_expired_registrations_endpoint(db: Session = Depends(get_db)):
    """Manual cleanup endpoint for expired pending registrations (admin use)"""
    count = cleanup_expired_pending_registrations(db)
    return {
        "message": f"Cleaned up {count} expired pending registrations",
        "cleaned_up": count
    }