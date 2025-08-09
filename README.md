# Democrasite

A FastAPI-based democratic voting platform that allows users to create topics with custom answers and vote on them.

## Features

- **Custom Topics**: Create topics with 1-1000 custom answers (not just Yes/No)
- **Access Control**: Public topics or private topics with user permissions
- **User Management**: Topic creators can manage access lists for private topics
- **Share Codes**: Secure 8-character codes instead of exposed database IDs
- **JWT Authentication**: Secure user registration and login
- **RESTful API**: Clean REST endpoints for all operations
- **Interactive CLI**: Command-line interface for easy testing and interaction
- **Comprehensive Testing**: Full test suite with VS Code integration

## Quick Start

### Running the Application

#### Option 1: Docker with SQLite (Development)

```bash
# Clone the repository
git clone <repository-url>
cd Democrasite

# Build and start with docker-compose (uses SQLite by default)
docker-compose up --build

# Or run in background
docker-compose up -d --build

# Stop the application
docker-compose down
```

#### Option 2: Docker with PostgreSQL (Production-like)

```bash
# Start PostgreSQL and the application (will be available on port 8001)
docker-compose --profile postgres up --build

# Populate with test data (optional)
docker-compose --profile postgres run --rm populate-db-postgres

# Stop everything
docker-compose --profile postgres down
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

# In a separate terminal, use the interactive CLI
python3 cli.py
```

The API will be available at:
- **SQLite (Development)**: `http://localhost:8000`
- **PostgreSQL (Production)**: `http://localhost:8001`

> **Note**: Both environments can run simultaneously since they use different ports. The CLI connects to port 8000 by default, so make sure the SQLite server is running for CLI usage.

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

#### Docker Commands

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

### API Documentation

Once running, visit:
- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /register` - Register new user (auto-login)
- `POST /login` - Login existing user

### Topics
- `POST /topics` - Create a new topic (public or private)
- `GET /topic/{share_code}` - Get topic details and vote results

### Voting
- `POST /topic/{share_code}/votes` - Vote on a topic

### User Management (Private Topics)
- `GET /topic/{share_code}/users` - View topic access list and votes (creator only)
- `POST /topic/{share_code}/users` - Add users to private topic access list (creator only)
- `DELETE /topic/{share_code}/users` - Remove users from access list and their votes (creator only)

## Usage Examples

### Creating a Public Topic
```json
POST /topics
{
  "title": "What's your favorite programming language?",
  "answers": ["Python", "JavaScript", "Rust", "Go"],
  "is_public": true
}
```

### Creating a Private Topic
```json
POST /topics
{
  "title": "Team Pizza Preference",
  "answers": ["Margherita", "Pepperoni", "Hawaiian"],
  "is_public": false,
  "allowed_users": ["alice", "bob", "charlie"]
}
```

### Voting
```json
POST /topic/ABC123XY/votes
{
  "choice": "Python"
}
```

### Managing Users (Private Topics)
```json
POST /topic/ABC123XY/users
{
  "usernames": ["dave", "eve"]
}
```

```json
DELETE /topic/ABC123XY/users
{
  "usernames": ["alice"]
}
```

## Interactive CLI

The CLI provides a user-friendly interface:

```bash
python3 cli.py
```

Features:
- User registration and login with persistent sessions
- Topic creation with guided prompts (public/private)
- Voting with answer validation
- View topic results and statistics
- **User Management**: Add/remove users from private topics
- Comprehensive error handling and user feedback

### CLI Menu Options:
1. **Register** - Create new account (auto-login)
2. **Login** - Sign into existing account
3. **Logout** - Clear session
4. **Create topic** - Interactive topic creation
5. **Vote on topic** - Cast votes with validation
6. **View topic** - See results and details
7. **Manage topic users** - Add/remove users (private topics only)
8. **Exit** - Quit application

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
- Topic creation (public/private with validation)
- Voting system with choice validation  
- User authentication and authorization
- Access control for private topics
- User management operations
- Data integrity and cascade operations

### Database
- **Development**: SQLite (`democrasite.db`) - file-based, simple setup
- **Production**: PostgreSQL - robust, scalable, production-ready
- Tables auto-created on startup
- Reset SQLite: `rm democrasite.db`
- Reset PostgreSQL: `docker-compose --profile postgres down --volumes`

## Architecture

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM with multi-database support (SQLite + PostgreSQL)
- **JWT** - Authentication with bcrypt password hashing
- **Pydantic** - Data validation and serialization
- **pytest** - Testing framework
- **Docker** - Containerization with profile-based environments

## License

MIT License