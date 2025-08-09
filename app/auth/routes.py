from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.schemas import UserCreate, UserLogin, Token, UserStats
from app.auth.utils import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    get_current_user
)
from app.config.settings import settings
from app.db.database import get_db
from app.db.models import User, Topic, Vote
from app.services.email_service import (
    email_service, 
    generate_verification_token, 
    get_token_expiration, 
    is_token_expired
)

router = APIRouter()

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user.username.lower()) | (User.email == user.email)
    ).first()
    
    if existing_user:
        if existing_user.username == user.username.lower():
            raise HTTPException(status_code=400, detail="Username already registered")
        else:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate verification token
    verification_token = generate_verification_token()
    token_expires = get_token_expiration()
    
    # Create user (unverified)
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username.lower(),
        email=user.email,
        hashed_password=hashed_password,
        email_verified=False,
        verification_token=verification_token,
        verification_token_expires=token_expires
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send verification email
    email_sent = email_service.send_verification_email(
        to_email=user.email,
        username=user.username,
        verification_token=verification_token
    )
    
    if not email_sent:
        # If email fails, still allow registration but warn user
        return {
            "message": "Registration successful! However, we couldn't send the verification email. Please contact support.",
            "email_sent": False,
            "username": user.username
        }
    
    return {
        "message": "Registration successful! Please check your email to verify your account before logging in.",
        "email_sent": True,
        "username": user.username
    }

@router.post("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user's email address using the verification token"""
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
    
    # Check if email is verified
    if not db_user.email_verified:
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
    
    # Check if email is verified
    if not db_user.email_verified:
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