from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.api.schemas import UserCreate, UserLogin, TopicCreate, VoteSubmit, Token, TopicResponse
from app.auth.utils import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    get_current_user
)
from app.config.settings import settings
from app.db.database import get_db
from app.db.models import User, Topic, Vote, TopicAccess

router = APIRouter()

@router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/topics")
def create_topic(
    topic: TopicCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    db_topic = Topic(
        title=topic.title, 
        created_by=current_user.id,
        answers=topic.answers,
        is_public=topic.is_public
    )
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    
    # Add allowed users for private topics
    if not topic.is_public and topic.allowed_users:
        for username in topic.allowed_users:
            user = db.query(User).filter(User.username == username).first()
            if user:
                access = TopicAccess(topic_id=db_topic.id, user_id=user.id)
                db.add(access)
        db.commit()
    
    return {"id": db_topic.id, "title": db_topic.title, "created_at": db_topic.created_at}

@router.post("/topic/{topic_id}/vote")
def submit_vote(
    topic_id: int,
    vote: VoteSubmit, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Check access permissions
    if not topic.is_public:
        access = db.query(TopicAccess).filter(
            TopicAccess.topic_id == topic_id,
            TopicAccess.user_id == current_user.id
        ).first()
        if not access and topic.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied to this private topic")
    
    # Validate choice is in available answers
    if vote.choice not in topic.answers:
        raise HTTPException(status_code=400, detail=f"Choice must be one of: {', '.join(topic.answers)}")
    
    existing_vote = db.query(Vote).filter(
        Vote.user_id == current_user.id, 
        Vote.topic_id == topic_id
    ).first()
    if existing_vote:
        existing_vote.choice = vote.choice
    else:
        db_vote = Vote(user_id=current_user.id, topic_id=topic_id, choice=vote.choice)
        db.add(db_vote)
    
    db.commit()
    return {"message": "Vote submitted successfully"}

@router.get("/topic/{topic_id}", response_model=TopicResponse)
def get_topic(
    topic_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Check access permissions
    if not topic.is_public:
        access = db.query(TopicAccess).filter(
            TopicAccess.topic_id == topic_id,
            TopicAccess.user_id == current_user.id
        ).first()
        if not access and topic.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied to this private topic")
    
    # Get vote breakdown
    votes = db.query(Vote).filter(Vote.topic_id == topic_id).all()
    vote_breakdown = {}
    for answer in topic.answers:
        vote_breakdown[answer] = sum(1 for vote in votes if vote.choice == answer)
    
    total_votes = len(votes)
    
    return TopicResponse(
        id=topic.id,
        title=topic.title,
        answers=topic.answers,
        is_public=topic.is_public,
        created_at=topic.created_at,
        total_votes=total_votes,
        vote_breakdown=vote_breakdown
    )

@router.get("/topics/{topic_id}/results")
def get_vote_results(
    topic_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Check access permissions
    if not topic.is_public:
        access = db.query(TopicAccess).filter(
            TopicAccess.topic_id == topic_id,
            TopicAccess.user_id == current_user.id
        ).first()
        if not access and topic.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied to this private topic")
    
    # Get vote breakdown for all answers
    votes = db.query(Vote).filter(Vote.topic_id == topic_id).all()
    vote_breakdown = {}
    for answer in topic.answers:
        vote_breakdown[answer] = sum(1 for vote in votes if vote.choice == answer)
    
    return {
        "topic_id": topic_id,
        "topic_title": topic.title,
        "results": vote_breakdown
    }

@router.get("/")
def read_root():
    return {"message": "Welcome to Democrasite API"}