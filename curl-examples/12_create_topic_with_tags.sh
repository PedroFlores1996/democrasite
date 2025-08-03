#!/bin/bash
# Create a public topic with tags for discovery

# Replace YOUR_TOKEN with actual token from login/register
TOKEN="YOUR_TOKEN"

echo "=== Creating Topic with Tags ==="
curl -X POST "http://localhost:8000/topics" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Best Programming Language 2024",
    "answers": ["Python", "JavaScript", "Rust", "Go", "TypeScript"],
    "is_public": true,
    "tags": ["programming", "technology", "coding", "development"]
  }'

echo -e "\n\n=== Creating Sports Topic ==="
curl -X POST "http://localhost:8000/topics" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Favorite Sport to Watch",
    "answers": ["Football", "Basketball", "Tennis", "Soccer"],
    "is_public": true,
    "tags": ["sports", "entertainment", "recreation"]
  }'

echo -e "\n\n=== Creating Music Topic ==="
curl -X POST "http://localhost:8000/topics" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Best Music Genre",
    "answers": ["Rock", "Jazz", "Hip-Hop", "Classical", "Electronic"],
    "is_public": true,
    "tags": ["music", "entertainment", "culture"]
  }'

echo ""
echo "Expected response: Topic created with share_code and tags for discovery"