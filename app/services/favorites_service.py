from typing import List, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import Topic, User


class FavoritesService:
    """Service for managing user favorites"""
    
    def get_user_favorites(self, db: Session, user: User) -> List[Dict]:
        """Get all favorites for a user"""
        # Refresh user to get latest favorite_topics relationship
        db.refresh(user)
        
        return [
            {
                'id': topic.id,
                'share_code': topic.share_code,
                'title': topic.title,
                'created_at': topic.created_at
            }
            for topic in user.favorite_topics
        ]
    
    def add_to_favorites(self, db: Session, topic: Topic, user: User) -> Dict[str, str]:
        """Add a topic to user's favorites"""
        # Check if already favorited
        if topic in user.favorite_topics:
            raise HTTPException(
                status_code=400,
                detail="Topic is already in favorites"
            )
        
        # Add to favorites using relationship
        user.favorite_topics.append(topic)
        
        # Update denormalized favorite count
        topic.favorite_count = (topic.favorite_count or 0) + 1
        
        db.commit()
        
        return {"message": "Topic added to favorites"}
    
    def remove_from_favorites(self, db: Session, topic: Topic, user: User) -> Dict[str, str]:
        """Remove a topic from user's favorites"""
        if topic not in user.favorite_topics:
            raise HTTPException(
                status_code=404,
                detail="Topic not found in favorites"
            )
        
        # Remove from favorites using relationship
        user.favorite_topics.remove(topic)
        
        # Update denormalized favorite count
        topic.favorite_count = max(0, (topic.favorite_count or 0) - 1)
        
        db.commit()
        
        return {"message": "Topic removed from favorites"}


# Singleton instance
favorites_service = FavoritesService()