#!/bin/bash
# Search and discover public topics

# Replace YOUR_TOKEN with actual token from login/register
TOKEN="YOUR_TOKEN"

# Basic search - get all public topics (paginated)
echo "=== Basic Search (All Public Topics) ==="
curl -X GET "http://localhost:8000/topics" \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== Search by Title ==="
# Search for topics containing "programming" in title
curl -X GET "http://localhost:8000/topics?title=programming" \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== Search by Tags ==="
# Search for topics with "technology" or "programming" tags
curl -X GET "http://localhost:8000/topics?tags=technology,programming" \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== Pagination Example ==="
# Get first page with 5 results per page
curl -X GET "http://localhost:8000/topics?page=1&limit=5" \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== Sort by Recent ==="
# Sort by most recently created
curl -X GET "http://localhost:8000/topics?sort=recent" \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== Combined Search ==="
# Search for recent programming topics
curl -X GET "http://localhost:8000/topics?title=programming&sort=recent&limit=10" \
  -H "Authorization: Bearer $TOKEN"

echo ""
echo "Expected response: Paginated list of public topics with filtering applied"