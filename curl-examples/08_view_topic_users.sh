#!/bin/bash
# View users with access to a private topic (creator only)

# Replace YOUR_TOKEN with actual token from login/register
# Replace SHARE_CODE with actual share code from topic creation
TOKEN="YOUR_TOKEN"
SHARE_CODE="ABC123XY"

curl -X GET "http://localhost:8000/topic/$SHARE_CODE/users" \
  -H "Authorization: Bearer $TOKEN"

echo ""
echo "Expected response: List of allowed users and their votes"