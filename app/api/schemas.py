from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict
from datetime import datetime

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
    allowed_users: Optional[List[str]] = None  # List of usernames
    
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
    answers: List[str]
    is_public: bool
    created_at: datetime
    total_votes: int
    vote_breakdown: Dict[str, int]
    
    class Config:
        from_attributes = True

class VoteSubmit(BaseModel):
    choice: str

class Token(BaseModel):
    access_token: str
    token_type: str