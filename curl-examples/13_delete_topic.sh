#!/bin/bash
# Delete a topic (creator only)

# Replace YOUR_TOKEN with actual token from login/register
# Replace SHARE_CODE with actual share code from topic creation
TOKEN="YOUR_TOKEN"
SHARE_CODE="ABC123XY"

echo "=== Deleting Topic ==="
curl -X DELETE "http://localhost:8000/topics/$SHARE_CODE" \
  -H "Authorization: Bearer $TOKEN"

echo ""
echo "Expected response: Deletion confirmation with counts of related data removed"
echo "Note: Only the topic creator can delete a topic"