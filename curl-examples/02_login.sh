#!/bin/bash
# Login with existing user

curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "password123"
  }'

echo ""
echo "Expected response: Access token for authentication"