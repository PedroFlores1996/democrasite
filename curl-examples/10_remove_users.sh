#!/bin/bash
# Remove users from a private topic (creator only)

# Replace YOUR_TOKEN with actual token from login/register
# Replace SHARE_CODE with actual share code from topic creation
TOKEN="YOUR_TOKEN"
SHARE_CODE="ABC123XY"

curl -X DELETE "http://localhost:8000/topic/$SHARE_CODE/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "usernames": ["alice"]
  }'

echo ""
echo "Expected response: Results showing removed users and votes deleted"