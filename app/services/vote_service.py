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
        
        # Validate choices
        for choice in vote_data.choices:
            self._validate_vote_choice(topic, choice)
        
        # Submit or update votes
        self._upsert_votes(db, topic, current_user.id, vote_data.choices)
        
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
    
    def get_user_votes(self, db: Session, topic_id: int, user_id: int) -> list[str]:
        """
        Get the current votes/choices for a specific user on a topic
        """
        votes = (
            db.query(Vote)
            .filter(Vote.topic_id == topic_id, Vote.user_id == user_id)
            .all()
        )
        return [vote.choice for vote in votes]
    
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
    
    def check_and_grant_access(self, db: Session, topic: Topic, current_user: User):
        """
        Check if user has access to topic. For private topics accessed via share code,
        automatically grant access by adding user to allowed list.
        """
        if topic.is_public:
            return  # Public topics don't need access control
        
        # Check if user already has access
        access = (
            db.query(TopicAccess)
            .filter(
                TopicAccess.topic_id == topic.id,
                TopicAccess.user_id == current_user.id
            )
            .first()
        )
        
        if not access:
            # Auto-add user to allowed list when accessing via share code
            new_access = TopicAccess(topic_id=topic.id, user_id=current_user.id)
            db.add(new_access)
            db.commit()
    
    def _validate_vote_choice(self, topic: Topic, choice: str):
        """
        Validate that the vote choice is valid for this topic
        """
        if choice not in topic.answers:
            raise HTTPException(
                status_code=400,
                detail=f"Choice must be one of: {', '.join(topic.answers)}"
            )
    
    def _upsert_votes(self, db: Session, topic: Topic, user_id: int, choices: list):
        """
        Insert new votes or update existing votes for multi-select topics
        """
        # Remove all existing votes for this user on this topic
        existing_votes = (
            db.query(Vote)
            .filter(Vote.user_id == user_id, Vote.topic_id == topic.id)
            .all()
        )
        
        # Count votes before deletion for denormalized counter update
        votes_before = len(existing_votes)
        
        # Delete existing votes
        for vote in existing_votes:
            db.delete(vote)
        
        # Flush to ensure deletions are committed before inserts
        db.flush()
        
        # Add new votes
        new_votes = []
        for choice in choices:
            if topic.allow_multi_select:
                # For multi-select, create one vote per choice
                new_vote = Vote(user_id=user_id, topic_id=topic.id, choice=choice)
                new_votes.append(new_vote)
                db.add(new_vote)
            else:
                # For single-select, only take the first choice
                new_vote = Vote(user_id=user_id, topic_id=topic.id, choice=choices[0])
                new_votes.append(new_vote)
                db.add(new_vote)
                break
        
        # Update denormalized vote count
        # For single-select: count is number of users who voted
        # For multi-select: count is number of individual vote choices
        if topic.allow_multi_select:
            topic.vote_count = (topic.vote_count or 0) - votes_before + len(new_votes)
        else:
            # Single-select: if user had no vote before, increment by 1
            if votes_before == 0:
                topic.vote_count = (topic.vote_count or 0) + 1
        
        db.commit()


# Singleton instance
vote_service = VoteService()