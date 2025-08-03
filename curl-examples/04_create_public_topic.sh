#!/bin/bash
# Create a public topic

# Replace YOUR_TOKEN with actual token from login/register
TOKEN="YOUR_TOKEN"

curl -X POST "http://localhost:8000/topics" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "What is your favorite programming language?",
    "answers": ["Python", "JavaScript", "Rust", "Go", "Java"],
    "is_public": true
  }'

echo ""
echo "Expected response: Topic with ID and share_code"