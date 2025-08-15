from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.db.models import Topic, User
from app.schemas import SortOption, TopicSummary, TopicsSearchResponse
from app.services.vote_service import vote_service


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
        Uses split query approach: public topics (from DB) + user's accessible private topics (from relationship).
        """
        # Get public topics with filters and sorting
        public_topics = self._get_public_topics(db, title, tags, sort)
        
        # Get user's accessible private topics (includes created topics)
        private_topics = self._get_user_accessible_topics(current_user, title, tags)
        
        # Combine and deduplicate
        all_topics = self._combine_and_deduplicate_topics(public_topics, private_topics)
        
        # Apply sorting to combined results if needed
        sorted_topics = self._apply_final_sorting(all_topics, sort)
        
        # Apply pagination
        total = len(sorted_topics)
        paginated_topics = self._paginate_topic_list(sorted_topics, page, limit)
        
        # Build response objects
        topic_summaries = self._build_topic_summaries(db, paginated_topics)
        
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
    
    def _get_public_topics(self, db: Session, title: Optional[str], tags: Optional[str], sort: SortOption) -> List[Topic]:
        """Get public topics with filters only - sorting applied later for consistency"""
        query = db.query(Topic).filter(Topic.is_public == True)
        
        # Add title/share code search filter
        if title:
            title_lower = title.lower()
            tag_condition = func.lower(func.json_extract(Topic.tags, '$')).like(f'%"{title_lower}"%')
            
            query = query.filter(
                or_(
                    Topic.title.ilike(f"%{title}%"),
                    Topic.share_code.ilike(f"%{title}%"),
                    tag_condition
                )
            )
        
        # Add tags filter
        if tags:
            query = self._add_tags_filter(query, tags)
        
        # No sorting here - will be applied consistently to combined results
        return query.all()
    
    def _get_user_accessible_topics(self, current_user: User, title: Optional[str], tags: Optional[str]) -> List[Topic]:
        """Get user's accessible private topics (created + granted access) and apply filters"""
        # Combine created topics and accessible topics, avoiding duplicates
        created_topic_ids = {t.id for t in current_user.created_topics}
        accessible_topic_ids = {t.id for t in current_user.accessible_topics}
        all_accessible_ids = created_topic_ids | accessible_topic_ids
        
        # Get all topics user has access to
        all_accessible_topics = []
        for topic in current_user.created_topics:
            all_accessible_topics.append(topic)
        
        for topic in current_user.accessible_topics:
            if topic.id not in created_topic_ids:  # Avoid duplicates
                all_accessible_topics.append(topic)
        
        # Apply filters in Python
        filtered_topics = all_accessible_topics
        
        if title:
            title_lower = title.lower()
            filtered_topics = [
                t for t in filtered_topics 
                if (title_lower in t.title.lower() or 
                    title_lower in t.share_code.lower() or
                    (t.tags and any(title_lower in tag.lower() for tag in t.tags)))
            ]
        
        if tags:
            tag_list = [tag.strip().lower() for tag in tags.split(",")]
            filtered_topics = [
                t for t in filtered_topics
                if t.tags and any(
                    any(search_tag in topic_tag.lower() for topic_tag in t.tags)
                    for search_tag in tag_list
                )
            ]
        
        return filtered_topics
    
    def _combine_and_deduplicate_topics(self, public_topics: List[Topic], private_topics: List[Topic]) -> List[Topic]:
        """Combine public and private topics, removing duplicates"""
        # Use a set to track IDs and avoid duplicates
        seen_ids = set()
        combined_topics = []
        
        # Add public topics first
        for topic in public_topics:
            if topic.id not in seen_ids:
                seen_ids.add(topic.id)
                combined_topics.append(topic)
        
        # Add private topics (skip if already in public topics)
        for topic in private_topics:
            if topic.id not in seen_ids:
                seen_ids.add(topic.id)
                combined_topics.append(topic)
        
        return combined_topics
    
    def _apply_final_sorting(self, topics: List[Topic], sort: SortOption) -> List[Topic]:
        """Apply sorting to the final combined topic list"""
        if sort == SortOption.recent:
            return sorted(topics, key=lambda t: t.created_at, reverse=True)
        elif sort == SortOption.favorites:
            return sorted(topics, key=lambda t: t.favorite_count or 0, reverse=True)
        elif sort == SortOption.alphabetical:
            return sorted(topics, key=lambda t: t.title.lower())
        else:  # popular or votes
            return sorted(topics, key=lambda t: t.vote_count or 0, reverse=True)
    
    def _paginate_topic_list(self, topics: List[Topic], page: int, limit: int) -> List[Topic]:
        """Apply pagination to a list of topics"""
        offset = (page - 1) * limit
        return topics[offset:offset + limit]
    
    def _add_tags_filter(self, query, tags: str):
        """Add tags filtering to the query"""
        tag_list = [tag.strip().lower() for tag in tags.split(",")]
        tag_conditions = []
        
        for tag in tag_list:
            # Use case-insensitive search by converting JSON field to lowercase
            tag_conditions.append(
                func.lower(func.json_extract(Topic.tags, '$')).like(f'%"{tag}"%')
            )
        
        return query.filter(or_(*tag_conditions))
    
    
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
                    description=topic.description,
                    share_code=topic.share_code,
                    created_at=topic.created_at,
                    total_votes=vote_service.get_total_votes(db, topic.id),  # Use accurate count
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