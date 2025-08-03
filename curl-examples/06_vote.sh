#!/bin/bash
# Vote on a topic

# Replace YOUR_TOKEN with actual token from login/register
# Replace SHARE_CODE with actual share code from topic creation
TOKEN="YOUR_TOKEN"
SHARE_CODE="ABC123XY"

curl -X POST "http://localhost:8000/topic/$SHARE_CODE/votes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "choice": "Python"
  }'

echo ""
echo "Expected response: Success message"