import secrets
import string
from fastapi import HTTPException


class TopicService:
    def generate_share_code(self) -> str:
        """Generate a secure random share code"""
        # Generate a random 8-character code using uppercase letters and digits
        # This avoids encryption complexity while being secure
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(8))

    def find_topic_by_share_code(self, share_code: str, db):
        """Find topic by share code using database lookup"""
        from app.db.models import Topic

        topic = db.query(Topic).filter(Topic.share_code == share_code).first()
        if not topic:
            raise HTTPException(status_code=404, detail="Invalid share code")
        return topic


# Singleton instance
topic_service = TopicService()
