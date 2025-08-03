from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas import (
    TopicCreate,
    VoteSubmit,
    TopicResponse,
    UserManagement,
    UserManagementResponse,
    TopicsSearchResponse,
    SortOption,
)
from app.auth.utils import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.services.topic_service import topic_service
from app.services.topic_creation_service import topic_creation_service
from app.services.topic_search_service import topic_search_service
from app.services.vote_service import vote_service
from app.services.topic_user_service import topic_user_service

router = APIRouter()


@router.post("/topics")
def create_topic(
    topic: TopicCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new topic with optional tags and user access control"""
    return topic_creation_service.create_topic(db, topic, current_user)


@router.get("/topics", response_model=TopicsSearchResponse)
def search_topics(
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    limit: int = Query(
        20, ge=1, le=100, description="Number of results per page (max 100)"
    ),
    title: Optional[str] = Query(None, description="Search in topic titles"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    sort: SortOption = Query(SortOption.popular, description="Sort order"),
    _: User = Depends(get_current_user),  # Require auth but don't use user
    db: Session = Depends(get_db),
):
    """
    Search and discover public topics with filtering and pagination.

    - **page**: Page number (starts at 1)
    - **limit**: Results per page (1-100, default 20)
    - **title**: Search for topics containing this text in title
    - **tags**: Filter by tags (comma-separated, e.g., "sports,politics")
    - **sort**: Sort by popularity (total votes), recent (newest first), or votes (alias for popular)
    """
    return topic_search_service.search_topics(db, page, limit, title, tags, sort)


@router.post("/topics/{share_code}/votes")
def submit_vote(
    share_code: str,
    vote: VoteSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit or update a vote on a topic"""
    topic = topic_service.find_topic_by_share_code(share_code, db)
    return vote_service.submit_vote(db, topic, vote, current_user)


@router.get("/topics/{share_code}", response_model=TopicResponse)
def get_topic(
    share_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get topic details including vote breakdown"""
    topic = topic_service.find_topic_by_share_code(share_code, db)
    
    # Check access permissions (reuse vote service logic)
    vote_service._check_voting_permissions(db, topic, current_user)
    
    # Get vote statistics
    vote_breakdown = vote_service.get_vote_breakdown(db, topic.id, topic.answers)
    total_votes = vote_service.get_total_votes(db, topic.id)

    return TopicResponse(
        id=topic.id,
        title=topic.title,
        answers=topic.answers,
        is_public=topic.is_public,
        created_at=topic.created_at,
        total_votes=total_votes,
        vote_breakdown=vote_breakdown,
        tags=topic.tags or [],
    )


@router.post("/topics/{share_code}/users", response_model=UserManagementResponse)
def add_users_to_topic(
    share_code: str,
    user_management: UserManagement,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add users to a private topic's access list"""
    topic = topic_service.find_topic_by_share_code(share_code, db)
    return topic_user_service.add_users_to_topic(db, topic, user_management, current_user)


@router.delete("/topics/{share_code}/users", response_model=UserManagementResponse)
def remove_users_from_topic(
    share_code: str,
    user_management: UserManagement,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove users from topic access list and their votes"""
    topic = topic_service.find_topic_by_share_code(share_code, db)
    return topic_user_service.remove_users_from_topic(db, topic, user_management, current_user)


@router.get("/topics/{share_code}/users")
def get_topic_users(
    share_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get list of users who have access to the topic"""
    topic = topic_service.find_topic_by_share_code(share_code, db)
    return topic_user_service.get_topic_users(db, topic, current_user)


@router.delete("/topics/{share_code}")
def delete_topic(
    share_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a topic and all related data (creator only)"""
    topic = topic_service.find_topic_by_share_code(share_code, db)
    return topic_user_service.delete_topic(db, topic, current_user)


@router.get("/")
def read_root():
    return {"message": "Welcome to Democrasite API"}
