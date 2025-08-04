from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict

from app.auth.utils import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.services.topic_service import topic_service
from app.services.favorites_service import favorites_service

router = APIRouter()


@router.get("/favorites", response_model=List[Dict])
def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's favorite topics"""
    return favorites_service.get_user_favorites(db, current_user)


@router.post("/favorites/{share_code}")
def add_to_favorites(
    share_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a topic to favorites"""
    topic = topic_service.find_topic_by_share_code(share_code, db)
    return favorites_service.add_to_favorites(db, topic, current_user)


@router.delete("/favorites/{share_code}")
def remove_from_favorites(
    share_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a topic from favorites"""
    topic = topic_service.find_topic_by_share_code(share_code, db)
    return favorites_service.remove_from_favorites(db, topic, current_user)