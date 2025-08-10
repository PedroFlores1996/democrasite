from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import User, PendingRegistration
from app.services.email_service import (
    email_service, 
    generate_verification_token, 
    get_token_expiration,
    is_token_expired
)


def verify_pending_registration(db: Session, token: str) -> dict:
    """Handle verification of pending registration (production mode)."""
    pending_registration = db.query(PendingRegistration).filter(
        PendingRegistration.verification_token == token
    ).first()
    
    if not pending_registration:
        return None  # No pending registration found
    
    # Check if token is expired
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
        hashed_password=pending_registration.hashed_password
        # Note: With staged registration, all users in DB are verified by definition
    )
    db.add(db_user)
    
    # Clean up the pending registration
    db.delete(pending_registration)
    db.commit()
    db.refresh(db_user)
    
    return {"message": "Email verified successfully! You can now log in."}


def resend_verification_to_pending_user(db: Session, email: str) -> dict:
    """Resend verification email to pending registration (production mode)."""
    pending_registration = db.query(PendingRegistration).filter(
        PendingRegistration.email == email
    ).first()
    
    if not pending_registration:
        return None  # No pending registration found
    
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


