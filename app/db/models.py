from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    votes = relationship("Vote", back_populates="user")
    created_topics = relationship("Topic", back_populates="creator")

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    answers = Column(JSON)  # List of available answers
    is_public = Column(Boolean, default=True)
    
    votes = relationship("Vote", back_populates="topic")
    creator = relationship("User", back_populates="created_topics")
    allowed_users = relationship("TopicAccess", back_populates="topic")

class TopicAccess(Base):
    __tablename__ = "topic_access"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('topic_id', 'user_id', name='unique_topic_user_access'),)
    
    topic = relationship("Topic", back_populates="allowed_users")
    user = relationship("User")

class Vote(Base):
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    choice = Column(String)  # Selected answer from topic's answers list
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('user_id', 'topic_id', name='unique_user_topic_vote'),)
    
    user = relationship("User", back_populates="votes")
    topic = relationship("Topic", back_populates="votes")