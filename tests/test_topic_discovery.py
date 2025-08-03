import pytest
from fastapi.testclient import TestClient


def test_create_topic_with_tags(client: TestClient, auth_headers):
    """Test creating a topic with tags"""
    topic_data = {
        "title": "Best Programming Language",
        "answers": ["Python", "JavaScript", "Rust"],
        "is_public": True,
        "tags": ["programming", "technology", "coding"]
    }
    
    response = client.post("/topics", json=topic_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "share_code" in data
    assert data["title"] == "Best Programming Language"


def test_search_topics_empty(client: TestClient, auth_headers):
    """Test searching topics when none exist"""
    response = client.get("/topics", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["topics"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["has_next"] is False
    assert data["has_prev"] is False


def test_search_topics_with_results(client: TestClient, auth_headers):
    """Test searching topics with results"""
    # Create test topics
    topics_data = [
        {
            "title": "Programming Languages Poll",
            "answers": ["Python", "Java", "Go"],
            "is_public": True,
            "tags": ["programming", "technology"]
        },
        {
            "title": "Sports Preferences", 
            "answers": ["Football", "Basketball", "Tennis"],
            "is_public": True,
            "tags": ["sports", "recreation"]
        }
    ]
    
    for topic_data in topics_data:
        response = client.post("/topics", json=topic_data, headers=auth_headers)
        assert response.status_code == 200
    
    # Search all topics
    response = client.get("/topics", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["topics"]) == 2
    assert data["total"] == 2
    assert data["has_next"] is False
    assert data["has_prev"] is False


def test_search_topics_by_title(client: TestClient, auth_headers):
    """Test searching topics by title"""
    # Create test topics
    topics_data = [
        {
            "title": "Programming Languages Poll",
            "answers": ["Python", "Java"],
            "is_public": True,
            "tags": ["programming"]
        },
        {
            "title": "Sports Preferences",
            "answers": ["Football", "Tennis"],
            "is_public": True,
            "tags": ["sports"]
        }
    ]
    
    for topic_data in topics_data:
        response = client.post("/topics", json=topic_data, headers=auth_headers)
        assert response.status_code == 200
    
    # Search by title
    response = client.get("/topics?title=programming", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["topics"]) == 1
    assert data["topics"][0]["title"] == "Programming Languages Poll"


def test_search_topics_by_tags(client: TestClient, auth_headers):
    """Test searching topics by tags"""
    # Create test topics
    topics_data = [
        {
            "title": "Programming Poll",
            "answers": ["Python", "Java"],
            "is_public": True,
            "tags": ["programming", "technology"]
        },
        {
            "title": "Sports Poll",
            "answers": ["Football", "Tennis"],
            "is_public": True,
            "tags": ["sports", "recreation"]
        }
    ]
    
    for topic_data in topics_data:
        response = client.post("/topics", json=topic_data, headers=auth_headers)
        assert response.status_code == 200
    
    # Search by tags
    response = client.get("/topics?tags=programming", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["topics"]) == 1
    assert data["topics"][0]["title"] == "Programming Poll"
    assert "programming" in data["topics"][0]["tags"]


def test_search_topics_pagination(client: TestClient, auth_headers):
    """Test topic search pagination"""
    # Create multiple test topics
    for i in range(5):
        topic_data = {
            "title": f"Test Topic {i+1}",
            "answers": ["Option A", "Option B"],
            "is_public": True,
            "tags": ["test"]
        }
        response = client.post("/topics", json=topic_data, headers=auth_headers)
        assert response.status_code == 200
    
    # Test first page with limit 3
    response = client.get("/topics?page=1&limit=3", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["topics"]) == 3
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["limit"] == 3
    assert data["has_next"] is True
    assert data["has_prev"] is False
    
    # Test second page
    response = client.get("/topics?page=2&limit=3", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["topics"]) == 2
    assert data["page"] == 2
    assert data["has_next"] is False
    assert data["has_prev"] is True


def test_search_topics_sorting(client: TestClient, auth_headers, test_user):
    """Test topic search sorting"""
    # Create test topic and vote on it
    topic_data = {
        "title": "Popular Topic",
        "answers": ["Yes", "No"],
        "is_public": True,
        "tags": ["test"]
    }
    
    response = client.post("/topics", json=topic_data, headers=auth_headers)
    assert response.status_code == 200
    share_code = response.json()["share_code"]
    
    # Vote on the topic to make it "popular"
    vote_data = {"choice": "Yes"}
    response = client.post(f"/topics/{share_code}/votes", json=vote_data, headers=auth_headers)
    assert response.status_code == 200
    
    # Create another topic (no votes)
    topic_data2 = {
        "title": "Unpopular Topic",
        "answers": ["Option A", "Option B"],
        "is_public": True,
        "tags": ["test"]
    }
    response = client.post("/topics", json=topic_data2, headers=auth_headers)
    assert response.status_code == 200
    
    # Search by popularity (default sort)
    response = client.get("/topics?sort=popular", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["topics"]) == 2
    # First topic should be the one with votes
    assert data["topics"][0]["title"] == "Popular Topic"
    assert data["topics"][0]["total_votes"] == 1


def test_search_only_public_topics(client: TestClient, auth_headers):
    """Test that search only returns public topics"""
    # Create a public topic
    public_topic = {
        "title": "Public Topic",
        "answers": ["Yes", "No"],
        "is_public": True,
        "tags": ["public"]
    }
    response = client.post("/topics", json=public_topic, headers=auth_headers)
    assert response.status_code == 200
    
    # Create a private topic
    private_topic = {
        "title": "Private Topic",
        "answers": ["Yes", "No"], 
        "is_public": False,
        "allowed_users": ["testuser"],
        "tags": ["private"]
    }
    response = client.post("/topics", json=private_topic, headers=auth_headers)
    assert response.status_code == 200
    
    # Search should only return public topics
    response = client.get("/topics", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["topics"]) == 1
    assert data["topics"][0]["title"] == "Public Topic"