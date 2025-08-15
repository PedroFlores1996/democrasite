from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import Topic, User, Vote
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
        Get list of users who have access to the topic using relationship
        """
        # Validate permissions
        self._validate_view_permissions(topic, current_user)
        
        # Get users with access via relationship
        users = topic.accessible_users
        
        # Get vote details
        user_votes = self._get_user_votes(db, topic.id, users)
        
        return {
            "topic_id": topic.id,
            "topic_title": topic.title,
            "creator": topic.creator.username,
            "users": [
                {
                    "username": user.username,
                    "vote_count": sum(1 for vote in db.query(Vote).filter(Vote.topic_id == topic.id, Vote.user_id == user.id).all())
                }
                for user in users
            ]
        }
    
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
        Process adding users to topic access list using relationship
        """
        added_users = []
        not_found_users = []
        already_added_users = []
        
        # Get the topic
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        
        for username in usernames:
            # Check if user exists
            user = db.query(User).filter(User.username == username).first()
            if not user:
                not_found_users.append(username)
                continue
            
            # Check if user already has access (via relationship)
            if user in topic.accessible_users:
                already_added_users.append(username)
                continue
            
            # Add user to accessible_users relationship
            topic.accessible_users.append(user)
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
        Process removing users from topic access list using relationship
        """
        removed_users = []
        not_found_users = []
        votes_removed = 0
        
        # Get the topic
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        
        for username in usernames:
            # Check if user exists
            user = db.query(User).filter(User.username == username).first()
            if not user:
                not_found_users.append(username)
                continue
            
            # Check if user has access and remove via relationship
            if user in topic.accessible_users:
                topic.accessible_users.remove(user)
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
        """Delete all access records for a topic using relationship"""
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            return 0
            
        access_count = len(topic.accessible_users)
        
        # Clear all users from the accessible_users relationship
        # This will delete the association table records
        topic.accessible_users.clear()
        
        return access_count
    
    def leave_topic(
        self,
        db: Session,
        topic: Topic,
        current_user: User
    ) -> Dict[str, str]:
        """
        Leave a private topic (remove user's access and votes)
        """
        # Only allow leaving private topics
        if topic.is_public:
            raise HTTPException(
                status_code=400,
                detail="Cannot leave public topics"
            )
        
        # Creator cannot leave their own topic
        if topic.created_by == current_user.id:
            raise HTTPException(
                status_code=400,
                detail="Topic creator cannot leave their own topic"
            )
        
        # Check if user has access to the topic (via relationship)
        if current_user not in topic.accessible_users:
            raise HTTPException(
                status_code=404,
                detail="You don't have access to this topic"
            )
        
        # Remove user's vote if they have one
        vote = (
            db.query(Vote)
            .filter(
                Vote.topic_id == topic.id,
                Vote.user_id == current_user.id
            )
            .first()
        )
        
        if vote:
            db.delete(vote)
            # Update denormalized vote count
            topic.vote_count = max(0, (topic.vote_count or 0) - 1)
        
        # Remove access via relationship
        topic.accessible_users.remove(current_user)
        db.commit()
        
        return {"message": f"You have left the topic '{topic.title}'"}


# Singleton instance
topic_user_service = TopicUserService()