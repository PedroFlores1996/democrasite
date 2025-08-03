#!/bin/bash
# Register a new user

curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "password123"
  }'

echo ""
echo "Expected response: Access token that you can use for authentication"