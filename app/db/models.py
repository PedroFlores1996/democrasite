from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Boolean, JSON, Table, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base

# Association table for User-Topic favorites (many-to-many)
user_topic_favorites = Table(
    'user_topic_favorites',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('topic_id', Integer, ForeignKey('topics.id'), primary_key=True),
    Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc))
)

# Association table for User-Topic access (many-to-many) - replaces TopicAccess entity
user_topic_access = Table(
    'user_topic_access',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('topic_id', Integer, ForeignKey('topics.id'), primary_key=True),
    Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc))
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)  # Specify length for better performance
    email = Column(String(255), unique=True, index=True)  # Email field for verification
    hashed_password = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    votes = relationship("Vote", back_populates="user")
    created_topics = relationship("Topic", back_populates="creator")
    favorite_topics = relationship("Topic", secondary=user_topic_favorites, back_populates="favorited_by")
    accessible_topics = relationship("Topic", secondary=user_topic_access, back_populates="accessible_users")

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), index=True)  # Specify reasonable length for title
    description = Column(Text, nullable=True)  # Optional topic description (better for PostgreSQL)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)  # Add index for sorting
    answers = Column(JSON)  # List of available answers
    is_public = Column(Boolean, default=True, index=True)  # Add index for filtering public topics
    is_editable = Column(Boolean, default=False)  # Allow others to add voting options
    allow_multi_select = Column(Boolean, default=False)  # Allow users to vote for multiple options
    share_code = Column(String(8), unique=True, index=True)  # Random 8-character share code
    tags = Column(JSON, default=list)  # List of tags for categorization and search
    vote_count = Column(Integer, default=0)  # Denormalized vote count for performance
    favorite_count = Column(Integer, default=0)  # Denormalized favorite count for business metrics
    
    votes = relationship("Vote", back_populates="topic")
    creator = relationship("User", back_populates="created_topics")
    favorited_by = relationship("User", secondary=user_topic_favorites, back_populates="favorite_topics")
    accessible_users = relationship("User", secondary=user_topic_access, back_populates="accessible_topics")

class PendingRegistration(Base):
    __tablename__ = "pending_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True)  # Not unique since we may have failed attempts
    email = Column(String(255), index=True)    # Not unique since we may have failed attempts
    hashed_password = Column(String(255))
    verification_token = Column(String(255), unique=True, index=True)  # Unique token for verification
    verification_token_expires = Column(DateTime)  # Token expiration
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Clean up expired registrations automatically
    __table_args__ = ()

class Vote(Base):
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    choice = Column(String(1000))  # Selected answer from topic's answers list
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # For multi-select topics, allow multiple votes per user per topic
    # The unique constraint will be enforced at the application level
    __table_args__ = (UniqueConstraint('user_id', 'topic_id', 'choice', name='unique_user_topic_choice'),)
    
    user = relationship("User", back_populates="votes")
    topic = relationship("Topic", back_populates="votes")

