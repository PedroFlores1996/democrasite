# PostgreSQL Setup and Testing Guide

This guide covers PostgreSQL setup, testing, and verification procedures for Democrasite.

## 🚀 Quick Start - PostgreSQL Setup

### Development Testing with Docker

```bash
# Start PostgreSQL and the app with PostgreSQL
docker-compose --profile postgres up -d

# The app will be available at http://localhost:8001 (port 8001 to avoid conflicts)
# PostgreSQL will be available at localhost:5432

# Populate with test data
docker-compose --profile postgres run --rm populate-db-postgres

# Stop everything
docker-compose --profile postgres down
```

### Production Environment Variables

Create a `.env` file for production:

```env
# Database credentials (CHANGE THESE!)
POSTGRES_USER=democrasite_user
POSTGRES_PASSWORD=super-secure-password-here

# Application secrets (CHANGE THESE!)
SECRET_KEY=your-super-secret-jwt-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email configuration (for production email verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Optional: Database URL override
# DATABASE_URL=postgresql://user:pass@localhost:5432/democrasite_db
```

### Production Deployment

```bash
# With environment file
docker-compose --profile postgres --env-file .env up -d

# Or with environment variables
POSTGRES_PASSWORD=secure-password SECRET_KEY=jwt-secret docker-compose --profile postgres up -d
```

## 🗄️ Database Migrations

For schema changes and migrations, see the dedicated [migrations documentation](./migrations/README.md).

### Quick Migration Commands

```bash
# Apply all pending migrations
alembic upgrade head

# Generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# View migration status
alembic current
alembic history
```

## 🔍 Verification & Testing

### 1. Test Database Connection

```bash
# Connect to PostgreSQL directly
docker-compose --profile postgres exec postgres psql -U democrasite_user -d democrasite_db

# List tables
\dt

# Check table schemas
\d topics
\d users
\d votes
\d pending_registrations

# Count records
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM topics;
SELECT COUNT(*) FROM votes;
SELECT COUNT(*) FROM pending_registrations;
```

### 2. Test Application Endpoints

```bash
# Health check (PostgreSQL app runs on port 8001)
curl http://localhost:8001/

# API docs (should work)
open http://localhost:8001/docs

# Register a test user (production mode - requires email verification)
curl -X POST "http://localhost:8001/api/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}'

# List topics
curl http://localhost:8001/api/topics
```

### 3. Test Staged Registration System

```bash
# Test registration in production mode (should use pending registration)
curl -X POST "http://localhost:8001/api/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "stagingtest", "email": "staging@example.com", "password": "password123"}'

# Verify no user was created if email fails
docker-compose --profile postgres exec postgres psql -U democrasite_user -d democrasite_db -c "SELECT username FROM users WHERE username = 'stagingtest';"

# Verify pending registration was cleaned up on failure
docker-compose --profile postgres exec postgres psql -U democrasite_user -d democrasite_db -c "SELECT username FROM pending_registrations WHERE username = 'stagingtest';"

# Test retry capability (should not get "already registered" error)
curl -X POST "http://localhost:8001/api/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "stagingtest", "email": "staging@example.com", "password": "password123"}'
```

### 4. Performance Comparison

```bash
# Time SQLite queries (development - port 8000)
time curl -s http://localhost:8000/api/topics > /dev/null

# Time PostgreSQL queries (production - port 8001)
time curl -s http://localhost:8001/api/topics > /dev/null
```

### 5. Email Verification Testing

```bash
# Test development mode (immediate user creation)
curl -X POST "http://localhost:8000/api/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "devtest", "email": "dev@example.com", "password": "password123"}'

# Should return: "requires_verification": false

# Test production mode (staged registration)  
curl -X POST "http://localhost:8001/api/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "prodtest", "email": "prod@example.com", "password": "password123"}'

# Should return: "requires_verification": true or email failure error
```

## 🚨 Common Issues & Solutions

### Issue 1: JSON Column Compatibility
**Problem**: SQLite and PostgreSQL handle JSON differently.

**Solution**: Our models use `Column(JSON)` which works with both. No changes needed.

### Issue 2: Boolean Column Defaults
**Problem**: SQLite uses 0/1 for booleans, PostgreSQL uses true/false.

**Solution**: SQLAlchemy handles this automatically. No changes needed.

### Issue 3: String Length Specifications
**Problem**: PostgreSQL prefers explicit string lengths for performance.

**Solution**: Already updated in our models:
- `username`: `String(50)`
- `email`: `String(255)` 
- `title`: `String(500)`
- `share_code`: `String(8)`
- `choice`: `String(1000)`

### Issue 4: Connection Pool Exhaustion
**Problem**: PostgreSQL connections may exhaust under load.

**Solution**: Configure connection pooling in production:

```python
# In database.py for production
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=settings.DATABASE_CONNECT_ARGS,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300
)
```

### Issue 5: Pending Registrations Table Missing
**Problem**: `relation "pending_registrations" does not exist`

**Solution**: Run migrations to create the table:
```bash
alembic upgrade head
```

### Issue 6: SMTP Configuration Warnings
**Problem**: Warnings about missing SMTP_USERNAME/SMTP_PASSWORD

**Solution**: Set environment variables or use .env file:
```bash
cp .env.example .env
# Edit .env with your SMTP credentials
docker-compose --profile postgres --env-file .env up -d
```

## 📈 Production Deployment Checklist

- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Set unique `SECRET_KEY`
- [ ] Configure SMTP credentials for email verification
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Configure firewall (close port 5432 to external access)
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Monitor connection pool usage
- [ ] Set up health checks
- [ ] Test email verification flow
- [ ] Test staged registration system
- [ ] Document recovery procedures

## 🔄 Environment Switching

### Switch to PostgreSQL (Production Mode)
```bash
# Stop SQLite setup if running
docker-compose down

# Start PostgreSQL setup
docker-compose --profile postgres up -d

# Apply migrations
docker-compose --profile postgres exec democrasite-postgres alembic upgrade head

# Populate with test data (optional)
docker-compose --profile postgres run --rm populate-db-postgres
```

### Switch Back to SQLite (Development Mode)
```bash
# Stop PostgreSQL setup
docker-compose --profile postgres down

# Start SQLite setup
docker-compose up -d

# Your SQLite data is preserved in the democrasite_db volume
```

## 📊 Database Schema Verification

### Check Current Schema
```sql
-- Connect to PostgreSQL
docker-compose --profile postgres exec postgres psql -U democrasite_user -d democrasite_db

-- View all tables
\dt

-- Check specific table schemas
\d users
\d topics  
\d votes
\d topic_access
\d user_topic_favorites
\d pending_registrations

-- Check constraints and indexes
\di pending_registrations
```

### Verify Migration Status
```bash
# Check current migration version
docker-compose --profile postgres exec democrasite-postgres alembic current

# View migration history
docker-compose --profile postgres exec democrasite-postgres alembic history

# Check for pending migrations
docker-compose --profile postgres exec democrasite-postgres alembic heads
```

## 📚 Further Reading

- [Database Migrations Guide](./migrations/README.md)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [SQLAlchemy PostgreSQL Dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [Docker PostgreSQL Best Practices](https://github.com/docker-library/docs/blob/master/postgres/README.md)
- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)