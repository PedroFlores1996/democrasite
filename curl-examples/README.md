# Democrasite API - cURL Examples

This folder contains example cURL commands for all Democrasite API endpoints.

## Quick Setup

1. **Start the server**: `python3 main.py`
2. **Make scripts executable**: `chmod +x curl-examples/*.sh`
3. **Get an auth token**: Run `./01_register.sh` or `./02_login.sh`
4. **Update token in scripts**: Replace `YOUR_TOKEN` with your actual token

## Authentication Flow

### Step 1: Register or Login
```bash
# Register new user (auto-login)
./01_register.sh

# OR login existing user  
./02_login.sh

# OR OAuth2 login (for Swagger UI)
./03_oauth_login.sh
```

Copy the `access_token` from the response.

### Step 2: Update Scripts
Edit the curl scripts and replace `YOUR_TOKEN` with your actual token:
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Available Examples

| Script | Endpoint | Description |
|--------|----------|-------------|
| `01_register.sh` | `POST /register` | Register new user |
| `02_login.sh` | `POST /login` | Login existing user |
| `03_oauth_login.sh` | `POST /token` | OAuth2 form login |
| `04_create_public_topic.sh` | `POST /topics` | Create public topic |
| `05_create_private_topic.sh` | `POST /topics` | Create private topic |
| `06_vote.sh` | `POST /topic/{share_code}/votes` | Vote on topic |
| `07_view_topic.sh` | `GET /topic/{share_code}` | View topic results |
| `08_view_topic_users.sh` | `GET /topic/{share_code}/users` | View topic users |
| `09_add_users.sh` | `POST /topic/{share_code}/users` | Add users to private topic |
| `10_remove_users.sh` | `DELETE /topic/{share_code}/users` | Remove users from topic |

## Usage Examples

### Complete Workflow
```bash
# 1. Register user
./01_register.sh

# 2. Create topic (copy the share_code from response)
./04_create_public_topic.sh  

# 3. Vote on topic (update SHARE_CODE first)
./06_vote.sh

# 4. View results
./07_view_topic.sh
```

### Private Topic Management
```bash
# 1. Create private topic
./05_create_private_topic.sh

# 2. Add more users  
./09_add_users.sh

# 3. View who has access
./08_view_topic_users.sh

# 4. Remove users if needed
./10_remove_users.sh
```

## Notes

- **Share Codes**: All topic operations use 8-character share codes (e.g., `ABC123XY`) instead of database IDs
- **Authentication**: Bearer token required for all operations except register/login
- **Private Topics**: User management only works on private topics and only for the creator
- **Vote Validation**: Votes must match one of the topic's predefined answers

## Alternative: FastAPI Docs

For interactive testing, visit `http://localhost:8000/docs` where you can:
- Use the "Authorize" button to set your Bearer token
- Test all endpoints with a user-friendly interface
- See request/response schemas automatically