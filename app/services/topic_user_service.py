from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import Topic, User, TopicAccess, Vote
from app.schemas import UserManagement, UserManagementResponse


class TopicUserService:
    """Service for managing topic user access"""
    
    def add_users_to_topic(
        self,
        db: Session,
        topic: Topic,
        user_management: UserManagement,
        current_user: User
    ) -> UserManagementResponse:
        """
        Add users to a private topic's access list
        """
        # Validate permissions
        self._validate_user_management_permissions(topic, current_user)
        
        # Process user additions
        results = self._process_user_additions(db, topic.id, user_management.usernames)
        
        db.commit()
        
        return UserManagementResponse(
            added_users=results["added"],
            not_found_users=results["not_found"],
            already_added_users=results["already_added"]
        )
    
    def remove_users_from_topic(
        self,
        db: Session,
        topic: Topic,
        user_management: UserManagement,
        current_user: User
    ) -> UserManagementResponse:
        """
        Remove users from topic access list and their votes
        """
        # Validate permissions
        self._validate_user_management_permissions(topic, current_user)
        
        # Process user removals
        results = self._process_user_removals(db, topic.id, user_management.usernames)
        
        db.commit()
        
        return UserManagementResponse(
            removed_users=results["removed"],
            not_found_users=results["not_found"],
            votes_removed=results["votes_removed"]
        )
    
    def get_topic_users(
        self,
        db: Session,
        topic: Topic,
        current_user: User
    ) -> Dict[str, Any]:
        """
        Get list of users who have access to the topic
        """
        # Validate permissions
        self._validate_view_permissions(topic, current_user)
        
        # Get users with access
        access_records = (
            db.query(TopicAccess)
            .filter(TopicAccess.topic_id == topic.id)
            .all()
        )
        user_ids = [access.user_id for access in access_records]
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        
        # Get vote details
        user_votes = self._get_user_votes(db, topic.id, users)
        
        return {
            "topic_id": topic.id,
            "topic_title": topic.title,
            "creator": topic.creator.username,
            "allowed_users": [user.username for user in users],
            "vote_details": user_votes
        }
    
    def _validate_user_management_permissions(self, topic: Topic, current_user: User):
        """
        Validate that user can manage topic access (admin operation - creator only)
        """
        if topic.created_by != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Only topic creator can manage user access"
            )
        
        if topic.is_public:
            raise HTTPException(
                status_code=400,
                detail="Cannot manage users on public topics - they can vote freely"
            )
    
    def _validate_view_permissions(self, topic: Topic, current_user: User):
        """
        Validate that user can view topic access list (admin operation - creator only)
        """
        if topic.created_by != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Only topic creator can view user access list"
            )
        
        if topic.is_public:
            raise HTTPException(
                status_code=400,
                detail="Public topics don't have access lists - anyone can vote"
            )
    
    def _process_user_additions(
        self,
        db: Session,
        topic_id: int,
        usernames: List[str]
    ) -> Dict[str, List[str]]:
        """
        Process adding users to topic access list
        """
        added_users = []
        not_found_users = []
        already_added_users = []
        
        for username in usernames:
            # Check if user exists
            user = db.query(User).filter(User.username == username).first()
            if not user:
                not_found_users.append(username)
                continue
            
            # Check if user already has access
            existing_access = (
                db.query(TopicAccess)
                .filter(
                    TopicAccess.topic_id == topic_id,
                    TopicAccess.user_id == user.id
                )
                .first()
            )
            
            if existing_access:
                already_added_users.append(username)
                continue
            
            # Add user access
            access = TopicAccess(topic_id=topic_id, user_id=user.id)
            db.add(access)
            added_users.append(username)
        
        return {
            "added": added_users,
            "not_found": not_found_users,
            "already_added": already_added_users
        }
    
    def _process_user_removals(
        self,
        db: Session,
        topic_id: int,
        usernames: List[str]
    ) -> Dict[str, Any]:
        """
        Process removing users from topic access list
        """
        removed_users = []
        not_found_users = []
        votes_removed = 0
        
        for username in usernames:
            # Check if user exists
            user = db.query(User).filter(User.username == username).first()
            if not user:
                not_found_users.append(username)
                continue
            
            # Remove access record
            access = (
                db.query(TopicAccess)
                .filter(
                    TopicAccess.topic_id == topic_id,
                    TopicAccess.user_id == user.id
                )
                .first()
            )
            
            if access:
                db.delete(access)
                removed_users.append(username)
            
            # Remove user's votes on this topic
            votes_removed += self._remove_user_votes(db, topic_id, user.id)
        
        return {
            "removed": removed_users,
            "not_found": not_found_users,
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
    
    def _get_user_votes(
        self,
        db: Session,
        topic_id: int,
        users: List[User]
    ) -> Dict[str, str]:
        """
        Get vote details for users with access to the topic
        """
        votes = db.query(Vote).filter(Vote.topic_id == topic_id).all()
        user_votes = {}
        
        for vote in votes:
            username = next(
                (user.username for user in users if user.id == vote.user_id),
                None
            )
            if username:
                user_votes[username] = vote.choice
        
        return user_votes

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
        """Delete all access records for a topic"""
        access_records = db.query(TopicAccess).filter(TopicAccess.topic_id == topic_id).all()
        access_count = len(access_records)
        
        for access in access_records:
            db.delete(access)
        
        return access_count


# Singleton instance
topic_user_service = TopicUserService()