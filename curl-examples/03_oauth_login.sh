#!/bin/bash
# OAuth2 form-based login (for Swagger UI compatibility)

curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=password123"

echo ""
echo "Expected response: Access token (same as /login but form-based)"