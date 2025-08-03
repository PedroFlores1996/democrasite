# Democrasite

A FastAPI-based democratic voting platform that allows users to create topics with custom answers and vote on them.

## Features

- **Custom Topics**: Create topics with 1-1000 custom answers (not just Yes/No)
- **Access Control**: Public topics or private topics with user permissions
- **User Management**: Topic creators can manage access lists for private topics
- **JWT Authentication**: Secure user registration and login
- **RESTful API**: Clean REST endpoints for all operations
- **Interactive CLI**: Command-line interface for easy testing and interaction
- **Comprehensive Testing**: Full test suite with VS Code integration

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Democrasite

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
# Start the FastAPI server
python3 main.py

# In a separate terminal, use the interactive CLI
python3 cli.py
```

The API will be available at `http://localhost:8000`

> **Note**: The CLI connects to the server, so make sure the server is running first.

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
- `GET /topic/{id}` - Get topic details and vote results

### Voting
- `POST /topic/{id}/votes` - Vote on a topic

### User Management (Private Topics)
- `GET /topic/{id}/users` - View topic access list and votes (creator only)
- `POST /topic/{id}/users` - Add users to private topic access list (creator only)
- `DELETE /topic/{id}/users` - Remove users from access list and their votes (creator only)

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
POST /topic/1/votes
{
  "choice": "Python"
}
```

### Managing Users (Private Topics)
```json
POST /topic/1/users
{
  "usernames": ["dave", "eve"]
}
```

```json
DELETE /topic/1/users
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
- Uses SQLite (`democrasite.db`)
- Tables auto-created on startup
- Reset: `rm democrasite.db`

## Architecture

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM with SQLite
- **JWT** - Authentication
- **Pydantic** - Data validation
- **pytest** - Testing framework

## License

MIT License