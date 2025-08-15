# Democrasite

A FastAPI-based democratic voting platform that allows users to create topics with custom answers and vote on them.

## Features

- **Custom Topics**: Create topics with 1-1000 custom answers (not just Yes/No)
- **Multi-Select Support**: Topics can allow single or multiple choice voting
- **Collaborative Topics**: Allow users to add new voting options to topics
- **Access Control**: Public topics (discoverable) or private topics (unlisted via share codes)
- **Share Codes**: Secure 8-character codes for topic access and sharing
- **Topic Management**: Edit descriptions, delete topics, and remove user access
- **JWT Authentication**: Secure user registration and login with optional email verification
- **RESTful API**: Clean REST endpoints for all operations
- **Comprehensive Testing**: Full test suite with VS Code integration

## Quick Start

### Running the Application

#### Option 1: Docker with SQLite (Development - No Email Verification)

```bash
# Clone the repository
git clone <repository-url>
cd Democrasite

# Build and start with docker-compose (uses SQLite, no email verification)
docker-compose up --build

# Or run in background
docker-compose up -d --build

# Stop the application
docker-compose down
```

**Features:**
- 🗃️ SQLite database (easy setup, no external dependencies)
- 🚀 No email verification required (instant registration & login)
- 🔧 Perfect for development, demos, and testing

#### Option 2: Docker with PostgreSQL (Production - Email Verification Required)

```bash
# Start PostgreSQL and the application (will be available on port 8001)
docker-compose --profile postgres up --build

# Populate with test data (optional)
docker-compose --profile postgres run --rm populate-db-postgres

# Stop everything
docker-compose --profile postgres down
```

**Features:**
- 🛡️ PostgreSQL database (production-ready, scalable)
- 📧 Email verification required (prevents spam registrations)  
- 🔒 Production-ready security configuration
- ⚙️ SMTP configuration needed (see environment setup below)

**Environment Setup for Production:**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your SMTP credentials
# SMTP_USERNAME=your-email@gmail.com
# SMTP_PASSWORD=your-app-password

# Then run with environment file
docker-compose --profile postgres --env-file .env up
```

#### Option 3: Local Development Only

```bash
# Clone the repository
git clone <repository-url>
cd Democrasite

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
python3 main.py
```

The API will be available at:
- **SQLite (Development)**: `http://localhost:8000`
- **PostgreSQL (Production)**: `http://localhost:8001`

> **Note**: Both environments can run simultaneously since they use different ports.

### Docker Compose Profiles

We use a single `docker-compose.yml` with profiles for different environments:
- **Default (no profile)**: SQLite development setup
- **`--profile postgres`**: PostgreSQL production setup
- **`--profile tools`**: Database population utilities

### Test Data Population

To test the application with realistic data, you can populate the database with comprehensive test data:

#### Local Development
```bash
# Populate database with test data
python3 populate_db.py
```

#### Docker Container (SQLite)
```bash
# Using the dedicated populate-db service
docker-compose --profile tools run --rm populate-db

# Or execute in running container
docker-compose exec democrasite python3 populate_db.py
```

#### Docker Container (PostgreSQL)
```bash
# Using the dedicated populate-db service for PostgreSQL
docker-compose --profile postgres run --rm populate-db-postgres

# Or execute in running PostgreSQL container
docker-compose --profile postgres exec democrasite-postgres python3 populate_db.py
```

This will create:
- **15 test users** with realistic usernames
- **20+ diverse topics** covering technology, entertainment, lifestyle, travel, etc.
- **Realistic voting patterns** (20-80% participation per topic)
- **Favorite relationships** between users and topics
- **Both public and private topics** for comprehensive testing

#### Test User Credentials
All test users have the password: `password123`

Sample usernames:
- `alice_cooper`
- `bob_builder` 
- `charlie_dev`
- `diana_explorer`
- `ethan_gamer`
- ... and 10 more

#### What Gets Created

**Topic Categories:**
- Technology (AI, programming, remote work)
- Entertainment (streaming, movies, gaming)
- Food & Lifestyle (coffee, vegetarian, health)
- Travel (camping, solo vs group travel)
- Education (skills, college, learning)
- Environment (sustainability, climate change)
- Sports (esports, Olympics, favorite sports)
- Private topics (team decisions, office polls)

**Realistic Data:**
- Topics created over the past 30 days
- Votes cast within a week of topic creation
- Varied participation rates per topic
- Favorite topics distributed across users
- Mix of public and private topics
- Some topics allow collaborative editing

> **💡 Pro tip**: After populating test data, try searching for tags like "camping", "technology", or "gaming" to see the search functionality in action!

### API Documentation

Once running, visit:
- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

All API endpoints are prefixed with `/api` (e.g., `/api/topics`, `/api/register`).

## API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/token` - Login existing user (OAuth2 form data)
- `GET /api/users/me` - Get current user profile
- `GET /api/users/me/stats` - Get user statistics
- `DELETE /api/users/me` - Delete user account

### Topics
- `POST /api/topics` - Create a new topic (public or private)
- `GET /api/topics` - Search and list topics (authenticated users only)
- `GET /api/topics/{share_code}` - Get topic details and vote results
- `PATCH /api/topics/{share_code}/description` - Update topic description (creator only)
- `DELETE /api/topics/{share_code}` - Delete topic and all related data (creator only)

### Voting
- `POST /api/topics/{share_code}/votes` - Submit vote(s) on a topic (supports single and multi-select)

### Topic Options (Collaborative Topics)
- `POST /api/topics/{share_code}/options` - Add new voting option to editable topic

### User Access Management
- `DELETE /api/topics/{share_code}/users/{username}` - Remove user from private topic (self-removal or creator removing others)

### Favorites
- `GET /api/favorites` - Get user's favorite topics
- `POST /api/favorites/{share_code}` - Add topic to favorites
- `DELETE /api/favorites/{share_code}` - Remove topic from favorites

## Usage Examples

### Authentication
```bash
# Register a new user
curl -X POST "http://localhost:8000/api/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "password": "password123"}'

# Login (returns JWT token)
curl -X POST "http://localhost:8000/api/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=password123"
```

### Creating Topics

#### Public Topic with Multi-Select
```json
POST /api/topics
Authorization: Bearer <jwt_token>
{
  "title": "What programming languages do you use regularly?",
  "description": "Select all that apply - we want to understand our team's tech stack",
  "answers": ["Python", "JavaScript", "Rust", "Go", "Java"],
  "is_public": true,
  "is_editable": false,
  "allow_multi_select": true,
  "tags": ["programming", "technology", "survey"]
}
```

#### Private Collaborative Topic
```json
POST /api/topics
Authorization: Bearer <jwt_token>
{
  "title": "Team Lunch Options",
  "description": "Suggest and vote on lunch spots for our team outing",
  "answers": ["Pizza Place", "Sushi Restaurant"],
  "is_public": false,
  "is_editable": true,
  "allow_multi_select": false,
  "tags": ["team", "food"]
}
```

### Voting

#### Single Choice Vote
```json
POST /api/topics/ABC123XY/votes
Authorization: Bearer <jwt_token>
{
  "choices": ["Python"]
}
```

#### Multi-Select Vote
```json
POST /api/topics/ABC123XY/votes
Authorization: Bearer <jwt_token>
{
  "choices": ["Python", "JavaScript", "Go"]
}
```

### Topic Management

#### Add Option to Collaborative Topic
```json
POST /api/topics/ABC123XY/options
Authorization: Bearer <jwt_token>
{
  "option": "Thai Restaurant"
}
```

#### Update Topic Description
```json
PATCH /api/topics/ABC123XY/description
Authorization: Bearer <jwt_token>
{
  "description": "Updated description with more context"
}
```

#### Remove User from Private Topic
```bash
# Creator removing another user
DELETE /api/topics/ABC123XY/users/bob
Authorization: Bearer <jwt_token>

# User removing themselves  
DELETE /api/topics/ABC123XY/users/alice
Authorization: Bearer <jwt_token>
```

### Search and Discovery

#### Search Topics
```bash
# Search by title and tags
GET /api/topics?title=programming&tags=technology&sort=popular&page=1&limit=20
Authorization: Bearer <jwt_token>

# Get all topics
GET /api/topics
Authorization: Bearer <jwt_token>
```

### Favorites Management
```bash
# Add to favorites
POST /api/favorites/ABC123XY
Authorization: Bearer <jwt_token>

# Remove from favorites
DELETE /api/favorites/ABC123XY
Authorization: Bearer <jwt_token>

# Get user's favorites
GET /api/favorites
Authorization: Bearer <jwt_token>
```

## Development

### Running Tests
```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test
python3 -m pytest tests/test_topics.py::test_create_topic_success -v

# VS Code: Use Test Explorer sidebar for debugging
```

### Key Features Tested:
- Topic creation (public/private with multi-select and collaborative options)
- Voting system with single and multi-choice validation
- User authentication and authorization
- Automatic access granting via share codes for private topics
- Topic management (description updates, deletion, user removal)
- Data integrity and cascade operations
- Search and filtering functionality
- Favorites system

### Database
- **Development**: SQLite (`democrasite.db`) - file-based, simple setup
- **Production**: PostgreSQL - robust, scalable, production-ready
- Tables auto-created on startup
- Reset SQLite: `rm democrasite.db`
- Reset PostgreSQL: `docker-compose --profile postgres down --volumes`

## Docker Commands

```bash
# Build the image
docker build -t democrasite .

# View logs (SQLite)
docker-compose logs -f democrasite

# View logs (PostgreSQL) 
docker-compose --profile postgres logs -f democrasite-postgres

# Access container shell (SQLite)
docker-compose exec democrasite bash

# Access container shell (PostgreSQL)
docker-compose --profile postgres exec democrasite-postgres bash

# Clean up everything
docker-compose down --volumes
docker-compose --profile postgres down --volumes
```

## Architecture

### Technology Stack
- **FastAPI** - Modern, fast web framework with automatic API documentation
- **SQLAlchemy** - ORM with multi-database support (SQLite + PostgreSQL)
- **JWT** - Stateless authentication with bcrypt password hashing
- **Pydantic** - Data validation and serialization with type hints
- **pytest** - Comprehensive testing framework with VS Code integration
- **Docker** - Containerization with profile-based environments

### Access Control Design

The platform uses a **simplified access control model** that recognizes the reality of how private topics work:

#### Public Topics
- **Discoverable**: Appear in search results and topic lists
- **Open Access**: Anyone can view and vote
- **Indexed**: Optimized for fast search and filtering

#### Private Topics (Unlisted)
- **Share Code Access**: Accessible only via direct share code URL
- **Automatic Access Granting**: Users gain access by visiting the share code URL
- **Persistent Access**: Once accessed, users can vote and revisit
- **Creator Controls**: Only creators can remove users or delete topics

#### Key Architectural Benefits
- **Honest UX**: No false promises about access control—share codes provide permanent access
- **Performance**: Split query approach separates public search (O(log n)) from private relationships
- **Simplicity**: Standard SQLAlchemy relationship patterns instead of complex access entities
- **Maintainability**: 346+ fewer lines of redundant user management code

#### User Removal
- **Creator Rights**: Topic creators can remove any user from private topics
- **Self-Removal**: Users can remove themselves from any private topic
- **Vote Cleanup**: Removing users also deletes their votes
- **Re-Access**: Removed users can regain access via the share code URL

This design acknowledges that "private" topics are effectively "unlisted" rather than truly secure, providing a cleaner and more honest user experience.

## License

MIT License