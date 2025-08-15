from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas import (
    TopicCreate,
    VoteSubmit,
    OptionAdd,
    TopicResponse,
    TopicsSearchResponse,
    SortOption,
    TopicDescriptionUpdate,
    TopicTagsUpdate,
)
from app.auth.utils import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.services.topic_service import topic_service
from app.services.topic_creation_service import topic_creation_service
from app.services.topic_search_service import topic_search_service
from app.services.vote_service import vote_service
from app.services.topic_user_service import topic_user_service
from app.services.topic_option_service import topic_option_service

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
    search: Optional[str] = Query(None, description="Search in topic titles and share codes"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    sort: SortOption = Query(SortOption.popular, description="Sort order"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search topics for authenticated users.
    Shows public topics + private topics user has access to.
    All topics require authentication to view.
    """
    return topic_search_service.search_topics(db, current_user, page, limit, search, tags, sort)


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
    
    # Check and grant access for private topics (auto-add via share code)
    vote_service.check_and_grant_access(db, topic, current_user)
    
    # Get vote statistics
    vote_breakdown = vote_service.get_vote_breakdown(db, topic.id, topic.answers)
    total_votes = vote_service.get_total_votes(db, topic.id)  # Use accurate count
    
    # Get current user's votes for this topic
    user_votes = vote_service.get_user_votes(db, topic.id, current_user.id)

    return TopicResponse(
        id=topic.id,
        title=topic.title,
        description=topic.description,
        share_code=topic.share_code,
        answers=topic.answers,
        is_public=topic.is_public,
        is_editable=topic.is_editable,
        allow_multi_select=getattr(topic, 'allow_multi_select', False),  # Default to False for existing topics
        created_at=topic.created_at,
        total_votes=total_votes,
        vote_breakdown=vote_breakdown,
        tags=topic.tags or [],
        created_by=topic.creator.username,
        user_votes=user_votes,
    )


@router.post("/topics/{share_code}/options")
def add_option_to_topic(
    share_code: str,
    option: OptionAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new voting option to an editable topic"""
    topic = topic_service.find_topic_by_share_code(share_code, db)
    return topic_option_service.add_option(db, topic, option, current_user)


@router.delete("/topics/{share_code}/users/{username}")
def remove_user_from_topic(
    share_code: str,
    username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a user from topic access list and their votes. Users can remove themselves, or topic creator can remove others."""
    topic = topic_service.find_topic_by_share_code(share_code, db)
    return topic_user_service.remove_single_user_from_topic(db, topic, username, current_user)


@router.patch("/topics/{share_code}/description")
def update_topic_description(
    share_code: str,
    description_update: TopicDescriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update topic description (creator only)"""
    topic = topic_service.find_topic_by_share_code(share_code, db)
    return topic_service.update_topic_description(db, topic, description_update, current_user)


@router.patch("/topics/{share_code}/tags")
def update_topic_tags(
    share_code: str,
    tags_update: TopicTagsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update topic tags (creator only)"""
    topic = topic_service.find_topic_by_share_code(share_code, db)
    return topic_service.update_topic_tags(db, topic, tags_update, current_user)


@router.delete("/topics/{share_code}")
def delete_topic(
    share_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a topic and all related data (creator only)"""
    topic = topic_service.find_topic_by_share_code(share_code, db)
    return topic_user_service.delete_topic(db, topic, current_user)




