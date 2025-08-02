# Democrasite

A FastAPI-based democratic voting platform that allows users to create topics with custom answers and vote on them.

## Features

- **Custom Topics**: Create topics with 1-1000 custom answers (not just Yes/No)
- **Access Control**: Public topics or private topics with user permissions
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

# Or use the interactive CLI
python3 cli.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /register` - Register new user (auto-login)
- `POST /login` - Login existing user

### Topics
- `POST /topics` - Create a new topic
- `GET /topic/{id}` - Get topic details and vote results

### Voting
- `POST /topic/{id}/vote` - Vote on a topic

## Usage Examples

### Creating a Topic
```json
POST /topics
{
  "title": "What's your favorite programming language?",
  "answers": ["Python", "JavaScript", "Rust", "Go"],
  "is_public": true
}
```

### Voting
```json
POST /topic/1/vote
{
  "choice": "Python"
}
```

## Interactive CLI

The CLI provides a user-friendly interface:

```bash
python3 cli.py
```

Features:
- User registration and login
- Topic creation with guided prompts
- Voting with answer validation
- View topic results
- Server management

## Development

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_topics.py::test_create_topic_success -v

# VS Code: Use Test Explorer sidebar for debugging
```

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