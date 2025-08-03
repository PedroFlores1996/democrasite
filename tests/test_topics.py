import pytest
from fastapi.testclient import TestClient


def test_create_topic_success(client: TestClient, auth_headers, sample_topic_data):
    """Test successful topic creation"""
    response = client.post("/topics", json=sample_topic_data, headers=auth_headers)
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "Test Topic"
    assert "created_at" in data


def test_create_topic_without_auth(client: TestClient, sample_topic_data):
    """Test topic creation without authentication fails"""
    response = client.post("/topics", json=sample_topic_data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 403


def test_create_topic_invalid_answers(client: TestClient, auth_headers):
    """Test topic creation with invalid answers"""
    invalid_data = {
        "title": "Invalid Topic",
        "answers": [],  # Empty answers should fail
        "is_public": True
    }
    
    response = client.post("/topics", json=invalid_data, headers=auth_headers)
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 422  # Validation error


def test_create_private_topic_success(client: TestClient, auth_headers, private_topic_data):
    """Test successful private topic creation"""
    response = client.post("/topics", json=private_topic_data, headers=auth_headers)
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "Private Test Topic"


def test_create_private_topic_no_allowed_users(client: TestClient, auth_headers):
    """Test private topic creation without allowed users fails"""
    invalid_data = {
        "title": "Private Topic No Users",
        "answers": ["Yes", "No"],
        "is_public": False,
        "allowed_users": []  # Private but no allowed users
    }
    
    response = client.post("/topics", json=invalid_data, headers=auth_headers)
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 422  # Validation error


def test_get_topic_success(client: TestClient, auth_headers, sample_topic_data):
    """Test getting topic details"""
    # First create a topic
    create_response = client.post("/topics", json=sample_topic_data, headers=auth_headers)
    assert create_response.status_code == 200
    topic_id = create_response.json()["id"]
    
    # Then get the topic
    response = client.get(f"/topic/{topic_id}", headers=auth_headers)
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == topic_id
    assert data["title"] == "Test Topic"
    assert data["answers"] == ["Option A", "Option B", "Option C"]
    assert data["is_public"] is True
    assert data["total_votes"] == 0
    assert "vote_breakdown" in data


def test_get_nonexistent_topic(client: TestClient, auth_headers):
    """Test getting a topic that doesn't exist"""
    response = client.get("/topic/999", headers=auth_headers)
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 404


def test_vote_on_topic_success(client: TestClient, auth_headers, sample_topic_data):
    """Test voting on a topic"""
    # First create a topic
    create_response = client.post("/topics", json=sample_topic_data, headers=auth_headers)
    assert create_response.status_code == 200
    topic_id = create_response.json()["id"]
    
    # Vote on the topic
    vote_data = {"choice": "Option A"}
    response = client.post(f"/topic/{topic_id}/votes", json=vote_data, headers=auth_headers)
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 200
    assert response.json()["message"] == "Vote submitted successfully"
    
    # Verify vote was recorded
    topic_response = client.get(f"/topic/{topic_id}", headers=auth_headers)
    topic_data = topic_response.json()
    assert topic_data["total_votes"] == 1
    assert topic_data["vote_breakdown"]["Option A"] == 1


def test_vote_invalid_choice(client: TestClient, auth_headers, sample_topic_data):
    """Test voting with invalid choice"""
    # First create a topic
    create_response = client.post("/topics", json=sample_topic_data, headers=auth_headers)
    assert create_response.status_code == 200
    topic_id = create_response.json()["id"]
    
    # Vote with invalid choice
    vote_data = {"choice": "Invalid Option"}
    response = client.post(f"/topic/{topic_id}/votes", json=vote_data, headers=auth_headers)
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 400