from typing import Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import Topic, Vote, TopicAccess, User
from app.schemas import VoteSubmit


class VoteService:
    """Service for handling voting operations"""
    
    def submit_vote(
        self,
        db: Session,
        topic: Topic,
        vote_data: VoteSubmit,
        current_user: User
    ) -> Dict[str, str]:
        """
        Submit or update a vote on a topic
        """
        # Check access permissions
        self._check_voting_permissions(db, topic, current_user)
        
        # Validate choice
        self._validate_vote_choice(topic, vote_data.choice)
        
        # Submit or update vote
        self._upsert_vote(db, topic.id, current_user.id, vote_data.choice)
        
        return {"message": "Vote submitted successfully"}
    
    def get_vote_breakdown(self, db: Session, topic_id: int, answers: list) -> Dict[str, int]:
        """
        Get vote breakdown for a topic
        """
        votes = db.query(Vote).filter(Vote.topic_id == topic_id).all()
        vote_breakdown = {}
        
        for answer in answers:
            vote_breakdown[answer] = sum(1 for vote in votes if vote.choice == answer)
        
        return vote_breakdown
    
    def get_total_votes(self, db: Session, topic_id: int) -> int:
        """
        Get total number of votes for a topic
        """
        return db.query(Vote).filter(Vote.topic_id == topic_id).count()
    
    def _check_voting_permissions(self, db: Session, topic: Topic, current_user: User):
        """
        Check if user can vote on this topic.
        For private topics, user must be in the allowed users list (which includes creator by default).
        """
        if not topic.is_public:
            access = (
                db.query(TopicAccess)
                .filter(
                    TopicAccess.topic_id == topic.id,
                    TopicAccess.user_id == current_user.id
                )
                .first()
            )
            if not access:
                raise HTTPException(
                    status_code=403, 
                    detail="Access denied to this private topic"
                )
    
    def _validate_vote_choice(self, topic: Topic, choice: str):
        """
        Validate that the vote choice is valid for this topic
        """
        if choice not in topic.answers:
            raise HTTPException(
                status_code=400,
                detail=f"Choice must be one of: {', '.join(topic.answers)}"
            )
    
    def _upsert_vote(self, db: Session, topic_id: int, user_id: int, choice: str):
        """
        Insert new vote or update existing vote
        """
        existing_vote = (
            db.query(Vote)
            .filter(Vote.user_id == user_id, Vote.topic_id == topic_id)
            .first()
        )
        
        if existing_vote:
            # Just updating choice, no need to change count
            existing_vote.choice = choice
        else:
            # New vote, increment the denormalized counter
            db_vote = Vote(user_id=user_id, topic_id=topic_id, choice=choice)
            db.add(db_vote)
            
            # Increment vote count on topic
            topic = db.query(Topic).filter(Topic.id == topic_id).first()
            if topic:
                topic.vote_count = (topic.vote_count or 0) + 1
        
        db.commit()


# Singleton instance
vote_service = VoteService()