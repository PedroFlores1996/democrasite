from pydantic import BaseModel, field_validator, EmailStr
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username must be between 3 and 50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower().strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class TopicCreate(BaseModel):
    title: str
    description: Optional[str] = None
    answers: List[str]
    is_public: bool = True
    is_editable: bool = False  # Allow others to add voting options
    allow_multi_select: bool = False  # Allow users to vote for multiple options
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
        # Private topics no longer require pre-defined allowed users
        # Users will be auto-added when they access via share code
        return v

class TopicResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    share_code: str
    answers: List[str]
    is_public: bool
    is_editable: bool
    allow_multi_select: bool
    created_at: datetime
    total_votes: int
    vote_breakdown: Dict[str, int]
    tags: List[str] = []
    created_by: str
    user_votes: List[str] = []  # Current user's votes/choices for this topic
    
    class Config:
        from_attributes = True

class VoteSubmit(BaseModel):
    choices: List[str]  # Support multiple choices for multi-select topics
    
    @field_validator('choices')
    @classmethod
    def validate_choices(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one choice must be selected')
        if len(v) > 100:  # Reasonable limit
            raise ValueError('Too many choices selected')
        return v

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

class TopicDescriptionUpdate(BaseModel):
    description: Optional[str] = None
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and len(v) > 2000:
            raise ValueError('Description must be 2000 characters or less')
        return v

class TopicTagsUpdate(BaseModel):
    tags: List[str]
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        
        cleaned_tags = []
        for tag in v:
            if not tag or not tag.strip():
                continue  # Skip empty tags
            cleaned_tag = tag.strip().upper()
            if len(cleaned_tag) > 50:
                raise ValueError('Each tag must be 50 characters or less')
            if cleaned_tag not in cleaned_tags:  # Avoid duplicates
                cleaned_tags.append(cleaned_tag)
        
        return cleaned_tags

# Topic Discovery & Search Schemas
class SortOption(str, Enum):
    popular = "popular"      # Most votes total
    recent = "recent"        # Most recently created
    votes = "votes"          # Most votes (alias for popular)
    favorites = "favorites"  # Most favorited
    alphabetical = "alphabetical"  # A-Z by title

class TopicSummary(BaseModel):
    """Lightweight topic info for search results"""
    id: int
    title: str
    description: Optional[str] = None
    share_code: str
    created_at: datetime
    total_votes: int
    answer_count: int
    favorite_count: int
    tags: List[str] = []
    creator_username: str
    is_public: bool
    is_favorited: bool = False
    
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

# User Profile & Stats Schemas
class UserStats(BaseModel):
    """User statistics for profile page"""
    username: str
    user_id: int
    created_at: datetime
    topics_created: int
    votes_cast: int
    favorite_topics: int