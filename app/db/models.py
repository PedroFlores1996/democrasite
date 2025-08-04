from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Boolean, JSON, Table
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

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    votes = relationship("Vote", back_populates="user")
    created_topics = relationship("Topic", back_populates="creator")
    favorite_topics = relationship("Topic", secondary=user_topic_favorites, back_populates="favorited_by")

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)  # Add index for sorting
    answers = Column(JSON)  # List of available answers
    is_public = Column(Boolean, default=True, index=True)  # Add index for filtering public topics
    is_editable = Column(Boolean, default=False)  # Allow others to add voting options
    share_code = Column(String, unique=True, index=True)  # Encrypted share code
    tags = Column(JSON, default=list)  # List of tags for categorization and search
    vote_count = Column(Integer, default=0)  # Denormalized vote count for performance
    favorite_count = Column(Integer, default=0)  # Denormalized favorite count for business metrics
    
    votes = relationship("Vote", back_populates="topic")
    creator = relationship("User", back_populates="created_topics")
    allowed_users = relationship("TopicAccess", back_populates="topic")
    favorited_by = relationship("User", secondary=user_topic_favorites, back_populates="favorite_topics")

class TopicAccess(Base):
    __tablename__ = "topic_access"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (UniqueConstraint('topic_id', 'user_id', name='unique_topic_user_access'),)
    
    topic = relationship("Topic", back_populates="allowed_users")
    user = relationship("User")

class Vote(Base):
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    choice = Column(String)  # Selected answer from topic's answers list
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (UniqueConstraint('user_id', 'topic_id', name='unique_user_topic_vote'),)
    
    user = relationship("User", back_populates="votes")
    topic = relationship("Topic", back_populates="votes")

