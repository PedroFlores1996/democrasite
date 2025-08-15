from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import Topic, User, Vote


class TopicUserService:
    """Service for topic deletion and user removal operations"""
    
    
    
    
    def remove_single_user_from_topic(
        self,
        db: Session,
        topic: Topic,
        username_to_remove: str,
        current_user: User
    ) -> Dict[str, Any]:
        """
        Remove a specific user from topic access list and their votes.
        Authorization: User can remove themselves, or topic creator can remove others.
        """
        # Validate basic permissions (private topic check)
        if topic.is_public:
            raise HTTPException(
                status_code=400,
                detail="Cannot manage users on public topics - they can vote freely"
            )
        
        # Find the user to be removed
        user_to_remove = db.query(User).filter(User.username == username_to_remove).first()
        if not user_to_remove:
            raise HTTPException(
                status_code=404,
                detail=f"User '{username_to_remove}' not found"
            )
        
        # Authorization logic: self-removal OR creator removing others
        is_self_removal = current_user.id == user_to_remove.id
        is_creator = topic.created_by == current_user.id
        
        if not (is_self_removal or is_creator):
            raise HTTPException(
                status_code=403,
                detail="You can only remove yourself, or if you're the topic creator, remove others"
            )
        
        # Creator cannot remove themselves (use leave_topic for that)
        if is_creator and is_self_removal:
            raise HTTPException(
                status_code=400,
                detail="Topic creator cannot remove themselves - use leave topic instead"
            )
        
        # Check if user has access to remove (via relationship)
        if user_to_remove not in topic.accessible_users:
            raise HTTPException(
                status_code=404,
                detail=f"User '{username_to_remove}' doesn't have access to this topic"
            )
        
        # Remove access via relationship
        topic.accessible_users.remove(user_to_remove)
        
        # Remove user's votes on this topic
        votes_removed = self._remove_user_votes(db, topic.id, user_to_remove.id)
        
        db.commit()
        
        return {
            "message": f"User '{username_to_remove}' removed from topic",
            "removed_user": username_to_remove,
            "votes_removed": votes_removed
        }
    
    
    
    def _remove_user_votes(self, db: Session, topic_id: int, user_id: int) -> int:
        """
        Remove all votes from a user on a specific topic
        """
        user_votes = (
            db.query(Vote)
            .filter(Vote.topic_id == topic_id, Vote.user_id == user_id)
            .all()
        )
        
        votes_count = len(user_votes)
        for vote in user_votes:
            db.delete(vote)
        
        return votes_count
    

    def delete_topic(
        self,
        db: Session,
        topic: Topic,
        current_user: User
    ) -> Dict[str, str]:
        """
        Delete a topic and all related data (admin operation - creator only)
        """
        # Validate that only creator can delete topic
        if topic.created_by != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Only topic creator can delete the topic"
            )
        
        # Delete all related data
        vote_count = self._delete_topic_votes(db, topic.id)
        access_count = self._delete_topic_access(db, topic.id)
        
        # Delete the topic itself
        db.delete(topic)
        db.commit()
        
        return {
            "message": f"Topic '{topic.title}' deleted successfully",
            "votes_deleted": vote_count,
            "access_records_deleted": access_count
        }
    
    def _delete_topic_votes(self, db: Session, topic_id: int) -> int:
        """Delete all votes for a topic"""
        votes = db.query(Vote).filter(Vote.topic_id == topic_id).all()
        vote_count = len(votes)
        
        for vote in votes:
            db.delete(vote)
        
        return vote_count
    
    def _delete_topic_access(self, db: Session, topic_id: int) -> int:
        """Delete all access records for a topic using relationship"""
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            return 0
            
        access_count = len(topic.accessible_users)
        
        # Clear all users from the accessible_users relationship
        # This will delete the association table records
        topic.accessible_users.clear()
        
        return access_count
    


# Singleton instance
topic_user_service = TopicUserService()