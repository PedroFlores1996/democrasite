import pytest
from fastapi.testclient import TestClient
from tests.conftest import create_test_user


def test_update_topic_tags_success(client: TestClient, db, auth_headers):
    """Test successful tag update by topic creator"""
    # Create a topic first
    topic_data = {
        "title": "Test Topic for Tag Editing",
        "description": "Testing tag editing functionality",
        "answers": ["Option 1", "Option 2", "Option 3"],
        "tags": ["INITIAL", "TEST", "SAMPLE"],
        "is_public": True
    }
    
    # Create topic
    response = client.post("/api/topics", json=topic_data, headers=auth_headers)
    assert response.status_code == 200
    topic = response.json()
    share_code = topic["share_code"]
    
    # Get topic details to verify initial tags
    response = client.get(f"/api/topics/{share_code}", headers=auth_headers)
    assert response.status_code == 200
    topic_details = response.json()
    assert topic_details["tags"] == ["INITIAL", "TEST", "SAMPLE"]
    
    # Update tags
    new_tags = ["UPDATED", "MODIFIED", "NEWTEST", "WORKING"]
    update_data = {"tags": new_tags}
    
    response = client.patch(f"/api/topics/{share_code}/tags", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    
    update_result = response.json()
    assert update_result["message"] == "Topic tags updated successfully"
    assert update_result["tags"] == new_tags
    
    # Verify tags were actually updated
    response = client.get(f"/api/topics/{share_code}", headers=auth_headers)
    assert response.status_code == 200
    updated_topic = response.json()
    assert updated_topic["tags"] == new_tags


def test_update_topic_tags_empty(client: TestClient, db, auth_headers):
    """Test updating topic with empty tags"""
    # Create a topic first
    topic_data = {
        "title": "Test Topic for Empty Tags",
        "answers": ["Yes", "No"],
        "tags": ["INITIAL", "TAG"],
        "is_public": True
    }
    
    response = client.post("/api/topics", json=topic_data, headers=auth_headers)
    assert response.status_code == 200
    share_code = response.json()["share_code"]
    
    # Update with empty tags
    update_data = {"tags": []}
    response = client.patch(f"/api/topics/{share_code}/tags", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    
    result = response.json()
    assert result["tags"] == []
    
    # Verify empty tags
    response = client.get(f"/api/topics/{share_code}", headers=auth_headers)
    assert response.status_code == 200
    updated_topic = response.json()
    assert updated_topic["tags"] == []


def test_update_topic_tags_cleaning(client: TestClient, db, auth_headers):
    """Test tag cleaning (whitespace, duplicates, case normalization)"""
    # Create a topic first
    topic_data = {
        "title": "Test Topic for Tag Cleaning",
        "answers": ["A", "B"],
        "tags": ["INITIAL"],
        "is_public": True
    }
    
    response = client.post("/api/topics", json=topic_data, headers=auth_headers)
    assert response.status_code == 200
    share_code = response.json()["share_code"]
    
    # Update with messy tags that need cleaning
    messy_tags = ["  tag1  ", "TAG2", "", "  ", "tag3", "tag1", "Tag3"]  # Duplicates, empty, whitespace, case
    update_data = {"tags": messy_tags}
    
    response = client.patch(f"/api/topics/{share_code}/tags", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    
    result = response.json()
    # Should clean up to unique, uppercase, no duplicates
    expected_tags = ["TAG1", "TAG2", "TAG3"]
    assert result["tags"] == expected_tags


def test_update_topic_tags_validation_errors(client: TestClient, db, auth_headers):
    """Test tag validation errors"""
    # Create a topic first
    topic_data = {
        "title": "Test Topic for Validation",
        "answers": ["A", "B"],
        "tags": ["INITIAL"],
        "is_public": True
    }
    
    response = client.post("/api/topics", json=topic_data, headers=auth_headers)
    assert response.status_code == 200
    share_code = response.json()["share_code"]
    
    # Test too many tags (over 10)
    too_many_tags = [f"TAG{i}" for i in range(11)]
    update_data = {"tags": too_many_tags}
    
    response = client.patch(f"/api/topics/{share_code}/tags", json=update_data, headers=auth_headers)
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("Maximum 10 tags allowed" in str(error) for error in error_detail)
    
    # Test tag too long (over 50 characters)
    long_tag = "A" * 51
    update_data = {"tags": [long_tag]}
    
    response = client.patch(f"/api/topics/{share_code}/tags", json=update_data, headers=auth_headers)
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("50 characters or less" in str(error) for error in error_detail)


def test_update_topic_tags_unauthorized(client: TestClient, db, auth_headers):
    """Test that non-creators cannot update tags"""
    # Create a topic with the first user
    topic_data = {
        "title": "Test Topic for Authorization",
        "answers": ["A", "B"],
        "tags": ["ORIGINAL"],
        "is_public": True
    }
    
    response = client.post("/api/topics", json=topic_data, headers=auth_headers)
    assert response.status_code == 200
    share_code = response.json()["share_code"]
    
    # Create a second user
    other_user = create_test_user(db, "otheruser", "other@example.com")
    
    # Create auth headers for the second user
    from app.auth.utils import create_access_token
    other_token = create_access_token(data={"sub": other_user.username})
    other_headers = {"Authorization": f"Bearer {other_token}"}
    
    # Try to update tags as the second user
    update_data = {"tags": ["HACKED", "UNAUTHORIZED"]}
    response = client.patch(f"/api/topics/{share_code}/tags", json=update_data, headers=other_headers)
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Only topic creator can update the tags"
    
    # Verify original tags unchanged
    response = client.get(f"/api/topics/{share_code}", headers=auth_headers)
    assert response.status_code == 200
    topic = response.json()
    assert topic["tags"] == ["ORIGINAL"]


def test_update_topic_tags_nonexistent_topic(client: TestClient, auth_headers):
    """Test updating tags for non-existent topic"""
    update_data = {"tags": ["TEST"]}
    response = client.patch("/api/topics/NOTFOUND/tags", json=update_data, headers=auth_headers)
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid share code"


def test_update_topic_tags_no_auth(client: TestClient, db):
    """Test updating tags without authentication"""
    # Create a topic first (need to use a different approach since we need auth to create)
    from app.db.models import User, Topic
    from app.auth.utils import get_password_hash
    from app.services.topic_service import topic_service
    
    # Create user directly in database
    user = User(
        username="directuser",
        email="direct@example.com",
        hashed_password=get_password_hash("password")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create topic directly in database
    topic = Topic(
        title="Direct Topic",
        answers=["A", "B"],
        tags=["DIRECT"],
        is_public=True,
        created_by=user.id,
        share_code=topic_service.generate_share_code()
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    
    # Try to update without auth
    update_data = {"tags": ["NOAUTH"]}
    response = client.patch(f"/api/topics/{topic.share_code}/tags", json=update_data)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"