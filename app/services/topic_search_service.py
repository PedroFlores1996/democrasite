from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from app.db.models import Topic, Vote, User
from app.schemas import SortOption, TopicSummary, TopicsSearchResponse


class TopicSearchService:
    """Service for searching and discovering topics"""
    
    def search_topics(
        self,
        db: Session,
        page: int = 1,
        limit: int = 20,
        title: Optional[str] = None,
        tags: Optional[str] = None,
        sort: SortOption = SortOption.popular
    ) -> TopicsSearchResponse:
        """
        Search public topics with filtering, pagination, and sorting
        """
        # Build the query
        query = self._build_search_query(db, title, tags, sort)
        
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
        title: Optional[str],
        tags: Optional[str],
        sort: SortOption
    ):
        """Build the base search query with filters and sorting"""
        # Start with public topics only
        query = db.query(Topic).filter(Topic.is_public == True)
        
        # Add title search filter
        if title:
            query = query.filter(Topic.title.ilike(f"%{title}%"))
        
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
        else:  # popular or votes
            # Subquery to count votes per topic
            vote_counts = (
                db.query(Vote.topic_id, func.count(Vote.id).label("vote_count"))
                .group_by(Vote.topic_id)
                .subquery()
            )
            
            return query.outerjoin(
                vote_counts, Topic.id == vote_counts.c.topic_id
            ).order_by(desc(func.coalesce(vote_counts.c.vote_count, 0)))
    
    def _paginate_query(self, query, page: int, limit: int):
        """Apply pagination to the query"""
        offset = (page - 1) * limit
        return query.offset(offset).limit(limit).all()
    
    def _build_topic_summaries(self, db: Session, topics: List[Topic]) -> List[TopicSummary]:
        """Build TopicSummary objects from Topic models"""
        topic_summaries = []
        
        for topic in topics:
            # Get vote count for this topic
            vote_count = (
                db.query(func.count(Vote.id))
                .filter(Vote.topic_id == topic.id)
                .scalar()
            )
            
            topic_summaries.append(
                TopicSummary(
                    id=topic.id,
                    title=topic.title,
                    share_code=topic.share_code,
                    created_at=topic.created_at,
                    total_votes=vote_count,
                    tags=topic.tags or [],
                    creator_username=topic.creator.username
                )
            )
        
        return topic_summaries


# Singleton instance
topic_search_service = TopicSearchService()