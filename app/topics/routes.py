from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas import TopicCreate, VoteSubmit, TopicResponse, UserManagement, UserManagementResponse
from app.auth.utils import get_current_user
from app.db.database import get_db
from app.db.models import User, Topic, Vote, TopicAccess
from app.services.topic_service import topic_service

router = APIRouter()

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
    
    # Generate and store share code for the new topic
    share_code = topic_service.generate_share_code()
    db_topic.share_code = share_code
    db.commit()
    db.refresh(db_topic)
    
    return {
        "id": db_topic.id, 
        "share_code": share_code,
        "title": db_topic.title, 
        "created_at": db_topic.created_at
    }

@router.post("/topics/{share_code}/votes")
def submit_vote(
    share_code: str,
    vote: VoteSubmit, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Find topic by share code
    topic = topic_service.find_topic_by_share_code(share_code, db)
    topic_id = topic.id
    
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

@router.get("/topics/{share_code}", response_model=TopicResponse)
def get_topic(
    share_code: str, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Find topic by share code
    topic = topic_service.find_topic_by_share_code(share_code, db)
    topic_id = topic.id
    
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

@router.post("/topics/{share_code}/users", response_model=UserManagementResponse)
def add_users_to_topic(
    share_code: str,
    user_management: UserManagement,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add users to a private topic's access list"""
    # Find topic by share code
    topic = topic_service.find_topic_by_share_code(share_code, db)
    topic_id = topic.id
    
    # Only topic creator can manage users
    if topic.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only topic creator can manage user access")
    
    # Only private topics have access lists
    if topic.is_public:
        raise HTTPException(status_code=400, detail="Cannot add users to public topics - they can vote freely")
    
    added_users = []
    not_found_users = []
    already_added_users = []
    
    for username in user_management.usernames:
        # Check if user exists
        user = db.query(User).filter(User.username == username).first()
        if not user:
            not_found_users.append(username)
            continue
        
        # Check if user already has access
        existing_access = db.query(TopicAccess).filter(
            TopicAccess.topic_id == topic_id,
            TopicAccess.user_id == user.id
        ).first()
        
        if existing_access:
            already_added_users.append(username)
            continue
        
        # Add user access
        access = TopicAccess(topic_id=topic_id, user_id=user.id)
        db.add(access)
        added_users.append(username)
    
    db.commit()
    
    return UserManagementResponse(
        added_users=added_users,
        not_found_users=not_found_users,
        already_added_users=already_added_users
    )

@router.delete("/topics/{share_code}/users", response_model=UserManagementResponse)
def remove_users_from_topic(
    share_code: str,
    user_management: UserManagement,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove users from topic access list and their votes"""
    # Find topic by share code
    topic = topic_service.find_topic_by_share_code(share_code, db)
    topic_id = topic.id
    
    # Only topic creator can manage users
    if topic.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only topic creator can manage users")
    
    # Only private topics have access lists
    if topic.is_public:
        raise HTTPException(status_code=400, detail="Cannot remove users from public topics")
    
    removed_users = []
    not_found_users = []
    votes_removed = 0
    
    for username in user_management.usernames:
        # Check if user exists
        user = db.query(User).filter(User.username == username).first()
        if not user:
            not_found_users.append(username)
            continue
        
        # Remove access record
        access = db.query(TopicAccess).filter(
            TopicAccess.topic_id == topic_id,
            TopicAccess.user_id == user.id
        ).first()
        
        if access:
            db.delete(access)
            removed_users.append(username)
        
        # Remove user's votes on this topic
        user_votes = db.query(Vote).filter(
            Vote.topic_id == topic_id,
            Vote.user_id == user.id
        ).all()
        
        for vote in user_votes:
            db.delete(vote)
            votes_removed += 1
    
    db.commit()
    
    return UserManagementResponse(
        removed_users=removed_users,
        not_found_users=not_found_users,
        votes_removed=votes_removed
    )

@router.get("/topics/{share_code}/users")
def get_topic_users(
    share_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of users who have access to the topic"""
    # Find topic by share code
    topic = topic_service.find_topic_by_share_code(share_code, db)
    topic_id = topic.id
    
    # Only topic creator can view user access list
    if topic.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only topic creator can view user access list")
    
    # Only private topics have access lists
    if topic.is_public:
        raise HTTPException(status_code=400, detail="Public topics don't have access lists - anyone can vote")
    
    # Get users with access
    access_records = db.query(TopicAccess).filter(TopicAccess.topic_id == topic_id).all()
    user_ids = [access.user_id for access in access_records]
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    
    # Also get votes from allowed users
    votes = db.query(Vote).filter(Vote.topic_id == topic_id).all()
    user_votes = {}
    for vote in votes:
        username = next((user.username for user in users if user.id == vote.user_id), None)
        if username:
            user_votes[username] = vote.choice
    
    return {
        "topic_id": topic_id,
        "topic_title": topic.title,
        "creator": topic.creator.username,
        "allowed_users": [user.username for user in users],
        "vote_details": user_votes
    }

@router.get("/")
def read_root():
    return {"message": "Welcome to Democrasite API"}