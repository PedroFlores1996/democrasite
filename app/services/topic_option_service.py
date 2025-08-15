from typing import Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import Topic, User
from app.schemas import OptionAdd


class TopicOptionService:
    """Service for adding options to existing topics"""
    
    def add_option(
        self,
        db: Session,
        topic: Topic,
        option_data: OptionAdd,
        current_user: User
    ) -> Dict[str, str]:
        """
        Add a new voting option to an editable topic
        """
        # Check if topic is editable
        if not topic.is_editable:
            raise HTTPException(
                status_code=403,
                detail="This topic does not allow adding new options"
            )
        
        # Check access permissions for private topics
        if not topic.is_public:
            self._check_access_permissions(db, topic, current_user)
        
        # Check if option already exists (case-insensitive)
        new_option = option_data.option.strip()
        existing_options = [opt.lower() for opt in topic.answers]
        
        if new_option.lower() in existing_options:
            raise HTTPException(
                status_code=400,
                detail="This option already exists"
            )
        
        # Add the new option - create new list to trigger SQLAlchemy update
        original_answers = topic.answers.copy()
        new_answers = original_answers + [new_option]
        topic.answers = new_answers
        
        # Force SQLAlchemy to recognize the change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(topic, 'answers')
        
        db.add(topic)
        db.commit()
        db.refresh(topic)
        
        return {
            "message": "Option added successfully",
            "option": new_option,
            "total_options": len(topic.answers)
        }
    
    def _check_access_permissions(self, db: Session, topic: Topic, current_user: User):
        """
        Check if user can access this private topic
        """
        # Creator always has access
        if topic.created_by == current_user.id:
            return
        
        # Check if user is in accessible users list via relationship
        if current_user not in topic.accessible_users:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this private topic"
            )


# Singleton instance
topic_option_service = TopicOptionService()