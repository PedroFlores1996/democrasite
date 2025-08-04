from typing import Dict, Any
from sqlalchemy.orm import Session

from app.db.models import Topic, User, TopicAccess
from app.schemas import TopicCreate
from app.services.topic_service import topic_service


class TopicCreationService:
    """Service for creating topics"""
    
    def create_topic(
        self,
        db: Session,
        topic_data: TopicCreate,
        current_user: User
    ) -> Dict[str, Any]:
        """
        Create a new topic with all related setup
        """
        # Create the topic
        db_topic = self._create_topic_record(db, topic_data, current_user)
        
        # Add allowed users for private topics (always include creator)
        if not topic_data.is_public:
            allowed_users = topic_data.allowed_users or []
            # Always ensure creator is in the allowed users list
            if current_user.username not in allowed_users:
                allowed_users.append(current_user.username)
            self._add_allowed_users(db, db_topic.id, allowed_users)
        
        # Generate and assign share code
        share_code = self._assign_share_code(db, db_topic)
        
        # Auto-favorite the topic for its creator
        self._auto_favorite_for_creator(db, db_topic, current_user)
        
        return {
            "id": db_topic.id,
            "share_code": share_code,
            "title": db_topic.title,
            "created_at": db_topic.created_at
        }
    
    def _create_topic_record(
        self,
        db: Session,
        topic_data: TopicCreate,
        current_user: User
    ) -> Topic:
        """
        Create and save the topic database record
        """
        db_topic = Topic(
            title=topic_data.title,
            created_by=current_user.id,
            answers=topic_data.answers,
            is_public=topic_data.is_public,
            is_editable=topic_data.is_editable,
            tags=topic_data.tags or []
        )
        
        db.add(db_topic)
        db.commit()
        db.refresh(db_topic)
        
        return db_topic
    
    def _add_allowed_users(
        self,
        db: Session,
        topic_id: int,
        allowed_usernames: list[str]
    ):
        """
        Add allowed users to private topic access list
        """
        for username in allowed_usernames:
            user = db.query(User).filter(User.username == username).first()
            if user:
                access = TopicAccess(topic_id=topic_id, user_id=user.id)
                db.add(access)
        
        db.commit()
    
    def _assign_share_code(self, db: Session, topic: Topic) -> str:
        """
        Generate and assign share code to topic
        """
        share_code = topic_service.generate_share_code()
        topic.share_code = share_code
        db.commit()
        db.refresh(topic)
        
        return share_code
    
    def _auto_favorite_for_creator(self, db: Session, topic: Topic, creator: User):
        """
        Automatically add the topic to the creator's favorites
        """
        # Add to favorites using relationship
        creator.favorite_topics.append(topic)
        
        # Update denormalized favorite count
        topic.favorite_count = 1  # Creator is first favorite
        
        db.commit()


# Singleton instance
topic_creation_service = TopicCreationService()