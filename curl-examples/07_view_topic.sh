#!/bin/bash
# View topic details and results

# Replace YOUR_TOKEN with actual token from login/register
# Replace SHARE_CODE with actual share code from topic creation
TOKEN="YOUR_TOKEN"
SHARE_CODE="ABC123XY"

curl -X GET "http://localhost:8000/topics/$SHARE_CODE" \
  -H "Authorization: Bearer $TOKEN"

echo ""
echo "Expected response: Topic details with vote breakdown"