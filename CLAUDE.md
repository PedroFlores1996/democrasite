# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Democrasite is a FastAPI-based voting platform that allows users to create topics with custom answers and vote on them. The system supports both public and private topics with access control.

## Development Commands

### Server Management
- **Start development server**: `python3 main.py`
- **Start with virtual environment**: `source venv/bin/activate && python main.py`
- **Docker development (SQLite, no email verification)**: `docker-compose up`
- **Docker production (PostgreSQL, email verification)**: `docker-compose --profile postgres up`

### Testing
- **Run all tests**: `python -m pytest tests/ -v`
- **Run specific test**: `python -m pytest tests/test_topics.py::test_create_topic_success -v`
- **Run with coverage**: `python -m pytest tests/ --cov=app`
- **Debug tests in VS Code**: Use Test Explorer sidebar (tests configured for venv)

### Interactive CLI
- **Launch CLI tool**: `python3 cli.py`
- **CLI provides**: User registration/login, topic creation, voting, and results viewing

### Database Management
- **Reset database**: `rm democrasite.db` (tables auto-created on startup)
- **View schema**: Check `app/db/models.py` for current structure

## Architecture

### Core Components

**FastAPI Application** (`main.py`)
- Single entry point that configures FastAPI app, includes router, and creates database tables
- Runs on `localhost:8000` by default

**Database Layer** (`app/db/`)
- **Models**: SQLAlchemy models with relationships between User, Topic, Vote, and TopicAccess
- **Database**: SQLite with session management and dependency injection
- **Key relationships**: Users can create topics and vote; topics can be public or private with explicit access control

**API Layer** (`app/api/`)
- **Routes**: RESTful endpoints for auth, topic management, and voting
- **Schemas**: Pydantic models with validation (supports 1-1000 custom answers per topic)
- **Key endpoints**: `POST /topics`, `GET /topic/{id}`, `POST /topic/{id}/vote`

**Authentication** (`app/auth/`)
- JWT-based auth with bcrypt password hashing
- Bearer token authentication required for all topic operations
- Email verification system with conditional enforcement (configurable for dev/prod environments)
- Professional email templates using Python's built-in smtplib

### Data Flow

1. **Topic Creation**: Users create topics with custom answers (1-1000) and set public/private access
2. **Access Control**: Private topics require explicit user permission via TopicAccess table
3. **Voting**: Users vote on topics using custom answers, with vote validation against topic's answer list
4. **Results**: Vote breakdown aggregated by answer choice with total counts

### Key Design Decisions

- **Custom Answers**: Topics support any number of custom answers (not just Yes/No)
- **Access Control**: Granular permission system for private topics
- **Vote Validation**: Ensures votes match topic's available answers
- **REST Design**: Vote endpoint follows resource pattern: `POST /topic/{id}/vote`

### Testing Strategy

- **Integration Tests**: Full API testing with in-memory SQLite database
- **Test Isolation**: Each test gets fresh database via fixtures
- **Authentication Testing**: Covers both authenticated and unauthenticated scenarios
- **VS Code Integration**: Tests discoverable in Test Explorer with debugging support

### Configuration

- **Settings**: Environment-based config in `app/config/settings.py`
- **Database**: SQLite with configurable URL (defaults to `democrasite.db`)
- **Security**: JWT secret configurable via `SECRET_KEY` environment variable
- **Email Verification**: Automatically configured based on Docker profile
  - **Default Docker profile** (SQLite): `REQUIRE_EMAIL_VERIFICATION=false` - Development mode, no email verification
  - **PostgreSQL Docker profile**: `REQUIRE_EMAIL_VERIFICATION=true` - Production mode, email verification required
  - **Manual override**: Set `REQUIRE_EMAIL_VERIFICATION` environment variable to override defaults