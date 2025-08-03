#!/bin/bash
# Create a private topic with allowed users

# Replace YOUR_TOKEN with actual token from login/register
TOKEN="YOUR_TOKEN"

curl -X POST "http://localhost:8000/topics" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Team Pizza Preference",
    "answers": ["Margherita", "Pepperoni", "Hawaiian", "Veggie"],
    "is_public": false,
    "allowed_users": ["alice", "bob", "charlie"]
  }'

echo ""
echo "Expected response: Topic with ID and share_code"