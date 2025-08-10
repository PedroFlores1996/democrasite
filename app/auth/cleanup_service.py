from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.models import User, PendingRegistration, Topic, Vote


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


def delete_user_data(db: Session, user: User) -> dict:
    """Delete all user data and associated records. Returns deletion statistics."""
    
    # Delete user's votes
    user_votes = db.query(Vote).filter(Vote.user_id == user.id).all()
    votes_deleted = len(user_votes)
    for vote in user_votes:
        db.delete(vote)
    
    # Delete user's topics (this will cascade to related votes and access records)
    user_topics = db.query(Topic).filter(Topic.created_by == user.id).all()
    topics_deleted = len(user_topics)
    for topic in user_topics:
        # Delete all votes for this topic
        topic_votes = db.query(Vote).filter(Vote.topic_id == topic.id).all()
        for vote in topic_votes:
            db.delete(vote)
        db.delete(topic)
    
    # Remove user from favorites relationships (SQLAlchemy will handle the association table)
    user.favorite_topics.clear()
    
    # Delete the user
    db.delete(user)
    db.commit()
    
    return {
        "message": "Account deleted successfully",
        "topics_deleted": topics_deleted,
        "votes_deleted": votes_deleted
    }