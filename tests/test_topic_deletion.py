import pytest
from fastapi.testclient import TestClient


def test_delete_topic_success(client: TestClient, auth_headers):
    """Test successful topic deletion by creator"""
    # Create a topic first
    topic_data = {
        "title": "Topic to Delete",
        "answers": ["Yes", "No"],
        "is_public": True,
        "tags": ["test"]
    }
    
    response = client.post("/api/topics", json=topic_data, headers=auth_headers)
    assert response.status_code == 200
    share_code = response.json()["share_code"]
    
    # Delete the topic
    response = client.delete(f"/api/topics/{share_code}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "deleted successfully" in data["message"]
    assert data["votes_deleted"] == 0
    assert data["access_records_deleted"] == 0


def test_delete_topic_with_votes_and_access(client: TestClient, auth_headers):
    """Test deleting topic with votes and access records"""
    # Create a private topic
    topic_data = {
        "title": "Private Topic to Delete",
        "answers": ["Option A", "Option B"],
        "is_public": False,
        "allowed_users": ["testuser"],
        "tags": ["test"]
    }
    
    response = client.post("/api/topics", json=topic_data, headers=auth_headers)
    assert response.status_code == 200
    share_code = response.json()["share_code"]
    
    # Vote on the topic
    vote_data = {"choices": ["Option A"]}
    response = client.post(f"/api/topics/{share_code}/votes", json=vote_data, headers=auth_headers)
    assert response.status_code == 200
    
    # Delete the topic
    response = client.delete(f"/api/topics/{share_code}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "deleted successfully" in data["message"]
    assert data["votes_deleted"] == 1
    assert data["access_records_deleted"] == 1  # Creator is automatically added to allowed users


def test_delete_topic_not_creator(client: TestClient, auth_headers, db):
    """Test that non-creator cannot delete topic"""
    # Create a topic
    topic_data = {
        "title": "Someone Else's Topic",
        "answers": ["Yes", "No"],
        "is_public": True
    }
    
    response = client.post("/api/topics", json=topic_data, headers=auth_headers)
    assert response.status_code == 200
    share_code = response.json()["share_code"]
    
    # Create another user directly in database for testing
    from tests.conftest import create_test_user
    from app.auth.utils import create_access_token
    
    other_user = create_test_user(db, "otheruser", "otheruser@example.com")
    other_token = create_access_token(data={"sub": other_user.username})
    other_headers = {"Authorization": f"Bearer {other_token}"}
    
    # Try to delete as other user
    response = client.delete(f"/api/topics/{share_code}", headers=other_headers)
    
    assert response.status_code == 403
    assert "Only topic creator can delete" in response.json()["detail"]


def test_delete_nonexistent_topic(client: TestClient, auth_headers):
    """Test deleting a topic that doesn't exist"""
    response = client.delete("/api/topics/INVALID123", headers=auth_headers)
    
    assert response.status_code == 404


def test_topic_not_accessible_after_deletion(client: TestClient, auth_headers):
    """Test that topic is not accessible after deletion"""
    # Create and delete a topic
    topic_data = {
        "title": "Topic to Delete",
        "answers": ["Yes", "No"],
        "is_public": True
    }
    
    response = client.post("/api/topics", json=topic_data, headers=auth_headers)
    assert response.status_code == 200
    share_code = response.json()["share_code"]
    
    # Delete the topic
    response = client.delete(f"/api/topics/{share_code}", headers=auth_headers)
    assert response.status_code == 200
    
    # Try to access the deleted topic
    response = client.get(f"/api/topics/{share_code}", headers=auth_headers)
    assert response.status_code == 404
    
    # Try to vote on the deleted topic
    vote_data = {"choices": ["Yes"]}
    response = client.post(f"/api/topics/{share_code}/votes", json=vote_data, headers=auth_headers)
    assert response.status_code == 404