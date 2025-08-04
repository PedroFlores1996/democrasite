from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TopicCreate(BaseModel):
    title: str
    answers: List[str]
    is_public: bool = True
    is_editable: bool = False  # Allow others to add voting options
    allowed_users: Optional[List[str]] = None  # List of usernames
    tags: Optional[List[str]] = []  # List of tags for categorization
    
    @field_validator('answers')
    @classmethod
    def validate_answers(cls, v):
        if len(v) < 1 or len(v) > 1000:
            raise ValueError('Must have between 1 and 1000 answers')
        return v
    
    @field_validator('allowed_users')
    @classmethod
    def validate_allowed_users(cls, v, info):
        if not info.data.get('is_public') and not v:
            raise ValueError('Private topics must have at least one allowed user')
        return v

class TopicResponse(BaseModel):
    id: int
    title: str
    share_code: str
    answers: List[str]
    is_public: bool
    is_editable: bool
    created_at: datetime
    total_votes: int
    vote_breakdown: Dict[str, int]
    tags: List[str] = []
    created_by: str
    
    class Config:
        from_attributes = True

class VoteSubmit(BaseModel):
    choice: str

class OptionAdd(BaseModel):
    option: str
    
    @field_validator('option')
    @classmethod
    def validate_option(cls, v):
        if not v or not v.strip():
            raise ValueError('Option cannot be empty')
        if len(v.strip()) > 200:
            raise ValueError('Option must be 200 characters or less')
        return v.strip()

class Token(BaseModel):
    access_token: str
    token_type: str

class UserManagement(BaseModel):
    usernames: List[str]
    
    @field_validator('usernames')
    @classmethod
    def validate_usernames(cls, v):
        if not v:
            raise ValueError('At least one username is required')
        return v

class UserManagementResponse(BaseModel):
    added_users: Optional[List[str]] = []
    removed_users: Optional[List[str]] = []
    not_found_users: Optional[List[str]] = []
    already_added_users: Optional[List[str]] = []
    votes_removed: Optional[int] = 0

# Topic Discovery & Search Schemas
class SortOption(str, Enum):
    popular = "popular"      # Most votes total
    recent = "recent"        # Most recently created
    votes = "votes"          # Most votes (alias for popular)

class TopicSummary(BaseModel):
    """Lightweight topic info for search results"""
    id: int
    title: str
    share_code: str
    created_at: datetime
    total_votes: int
    answer_count: int
    tags: List[str] = []
    creator_username: str
    is_public: bool
    
    class Config:
        from_attributes = True

class TopicsSearchResponse(BaseModel):
    """Paginated response for topic search"""
    topics: List[TopicSummary]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool