from typing import Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import Topic, Vote, User
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
        Get total number of votes for a topic (count distinct users who voted)
        """
        from sqlalchemy import func
        return db.query(func.count(Vote.user_id.distinct())).filter(Vote.topic_id == topic_id).scalar()
    
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
        For private topics, user must be in the accessible users list or be the creator.
        """
        if not topic.is_public:
            # Check if user has access via relationship or is the creator
            has_access = (current_user in topic.accessible_users or 
                         topic.created_by == current_user.id)
            
            if not has_access:
                raise HTTPException(
                    status_code=403, 
                    detail="Access denied to this private topic"
                )
    
    def check_and_grant_access(self, db: Session, topic: Topic, current_user: User):
        """
        Check if user has access to topic. For private topics accessed via share code,
        automatically grant access by adding user to accessible users list.
        """
        if topic.is_public:
            return  # Public topics don't need access control
        
        # Check if user already has access (creator always has access)
        if topic.created_by == current_user.id:
            return  # Creator always has access
            
        # Check if user already has access via relationship
        if current_user not in topic.accessible_users:
            # Auto-add user to accessible list when accessing via share code
            topic.accessible_users.append(current_user)
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
        # For both single-select and multi-select: count is number of users who voted
        if votes_before == 0:
            # User didn't vote before, increment by 1
            topic.vote_count = (topic.vote_count or 0) + 1
        # If user already voted (votes_before > 0), the count stays the same
        
        db.commit()


# Singleton instance
vote_service = VoteService()