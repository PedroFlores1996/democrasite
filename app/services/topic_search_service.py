from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from app.db.models import Topic, User, TopicAccess
from app.schemas import SortOption, TopicSummary, TopicsSearchResponse


class TopicSearchService:
    """Service for searching and discovering topics"""
    
    def search_topics(
        self,
        db: Session,
        current_user: User,
        page: int = 1,
        limit: int = 20,
        title: Optional[str] = None,
        tags: Optional[str] = None,
        sort: SortOption = SortOption.popular
    ) -> TopicsSearchResponse:
        """
        Search topics for authenticated user with filtering, pagination, and sorting.
        Shows: public topics + private topics user created + private topics user has access to.
        """
        # Build the query
        query = self._build_search_query(db, current_user, title, tags, sort)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination and get results
        topics = self._paginate_query(query, page, limit)
        
        # Build response objects
        topic_summaries = self._build_topic_summaries(db, topics)
        
        # Calculate pagination info
        has_next = (page * limit) < total
        has_prev = page > 1
        
        return TopicsSearchResponse(
            topics=topic_summaries,
            total=total,
            page=page,
            limit=limit,
            has_next=has_next,
            has_prev=has_prev
        )
    
    def _build_search_query(
        self,
        db: Session,
        current_user: User,
        title: Optional[str],
        tags: Optional[str],
        sort: SortOption
    ):
        """Build the base search query with filters and sorting"""
        # Show public topics + private topics user has access to + topics created by user
        query = db.query(Topic).filter(
            or_(
                Topic.is_public == True,  # Public topics
                Topic.created_by == current_user.id,  # Topics created by user
                Topic.id.in_(  # Private topics user has access to
                    db.query(TopicAccess.topic_id)
                    .filter(TopicAccess.user_id == current_user.id)
                )
            )
        )
        
        # Add title and share code search filter
        if title:
            query = query.filter(
                or_(
                    Topic.title.ilike(f"%{title}%"),
                    Topic.share_code.ilike(f"%{title}%")
                )
            )
        
        # Add tags filter
        if tags:
            query = self._add_tags_filter(query, tags)
        
        # Add sorting
        query = self._add_sorting(db, query, sort)
        
        return query
    
    def _add_tags_filter(self, query, tags: str):
        """Add tags filtering to the query"""
        tag_list = [tag.strip().lower() for tag in tags.split(",")]
        tag_conditions = []
        
        for tag in tag_list:
            tag_conditions.append(
                func.json_extract(Topic.tags, '$').like(f'%"{tag}"%')
            )
        
        return query.filter(or_(*tag_conditions))
    
    def _add_sorting(self, db: Session, query, sort: SortOption):
        """Add sorting to the query"""
        if sort == SortOption.recent:
            return query.order_by(desc(Topic.created_at))
        elif sort == SortOption.favorites:
            # Sort by favorite count
            return query.order_by(desc(Topic.favorite_count))
        else:  # popular or votes
            # Use denormalized vote_count for sorting
            return query.order_by(desc(Topic.vote_count))
    
    def _paginate_query(self, query, page: int, limit: int):
        """Apply pagination to the query"""
        offset = (page - 1) * limit
        return query.offset(offset).limit(limit).all()
    
    def _build_topic_summaries(self, db: Session, topics: List[Topic]) -> List[TopicSummary]:
        """Build TopicSummary objects from Topic models"""
        topic_summaries = []
        
        for topic in topics:
            topic_summaries.append(
                TopicSummary(
                    id=topic.id,
                    title=topic.title,
                    share_code=topic.share_code,
                    created_at=topic.created_at,
                    total_votes=topic.vote_count or 0,  # Use denormalized count
                    answer_count=len(topic.answers) if topic.answers else 0,
                    favorite_count=topic.favorite_count or 0,  # Use denormalized count
                    tags=topic.tags or [],
                    creator_username=topic.creator.username,
                    is_public=topic.is_public
                )
            )
        
        return topic_summaries


# Singleton instance
topic_search_service = TopicSearchService()