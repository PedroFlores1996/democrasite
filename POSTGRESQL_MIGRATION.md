# PostgreSQL Migration Guide

This guide walks you through migrating Democrasite from SQLite to PostgreSQL for production use.

## 🚀 Quick Start - Testing PostgreSQL Locally

### Option 1: Test with Docker Compose Profiles

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

### Option 2: Production Setup Locally (Alternative)

```bash
# Same as Option 1 - we now use profiles in single docker-compose.yml
docker-compose --profile postgres up -d

# Populate with test data
docker-compose --profile postgres run --rm populate-db-postgres

# App available at http://localhost:8001 (port 8001 to avoid conflicts)
# Stop with: docker-compose --profile postgres down
```

## 🔧 Configuration

### Environment Variables for Production

Create a `.env` file for production:

```env
# Database credentials (CHANGE THESE!)
POSTGRES_USER=democrasite_user
POSTGRES_PASSWORD=super-secure-password-here

# Application secrets (CHANGE THESE!)
SECRET_KEY=your-super-secret-jwt-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

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

## 📊 Data Migration Strategy

### Method 1: Export/Import (Recommended for Small Datasets)

```bash
# 1. Export data from SQLite
docker-compose exec democrasite python3 -c "
from app.db.database import SessionLocal
from app.db.models import User, Topic, Vote, TopicAccess
import json

db = SessionLocal()

# Export users
users = db.query(User).all()
users_data = [{'id': u.id, 'username': u.username, 'hashed_password': u.hashed_password, 'created_at': u.created_at.isoformat()} for u in users]

# Export topics
topics = db.query(Topic).all()
topics_data = [{'id': t.id, 'title': t.title, 'description': t.description, 'created_by': t.created_by, 'created_at': t.created_at.isoformat(), 'answers': t.answers, 'is_public': t.is_public, 'is_editable': t.is_editable, 'allow_multi_select': t.allow_multi_select, 'share_code': t.share_code, 'tags': t.tags} for t in topics]

# Export votes
votes = db.query(Vote).all()
votes_data = [{'id': v.id, 'user_id': v.user_id, 'topic_id': v.topic_id, 'choice': v.choice, 'created_at': v.created_at.isoformat()} for v in votes]

# Save to JSON
with open('/app/data/export.json', 'w') as f:
    json.dump({'users': users_data, 'topics': topics_data, 'votes': votes_data}, f, indent=2)

print('Data exported to /app/data/export.json')
"

# 2. Import data into PostgreSQL
docker-compose --profile postgres exec democrasite-postgres python3 -c "
import json
from app.db.database import SessionLocal
from app.db.models import User, Topic, Vote, TopicAccess
from datetime import datetime
from sqlalchemy import text

# Read exported data
with open('/app/data/export.json', 'r') as f:
    data = json.load(f)

db = SessionLocal()

# Import users
for user_data in data['users']:
    user = User(
        username=user_data['username'],
        hashed_password=user_data['hashed_password'],
        created_at=datetime.fromisoformat(user_data['created_at'])
    )
    db.add(user)

# Import topics  
for topic_data in data['topics']:
    topic = Topic(
        title=topic_data['title'],
        description=topic_data.get('description'),
        created_by=topic_data['created_by'],
        created_at=datetime.fromisoformat(topic_data['created_at']),
        answers=topic_data['answers'],
        is_public=topic_data['is_public'],
        is_editable=topic_data['is_editable'],
        allow_multi_select=topic_data['allow_multi_select'],
        share_code=topic_data['share_code'],
        tags=topic_data['tags']
    )
    db.add(topic)

# Import votes
for vote_data in data['votes']:
    vote = Vote(
        user_id=vote_data['user_id'],
        topic_id=vote_data['topic_id'],
        choice=vote_data['choice'],
        created_at=datetime.fromisoformat(vote_data['created_at'])
    )
    db.add(vote)

db.commit()
print('Data imported successfully')
"
```

### Method 2: Fresh Start (Recommended)

```bash
# Simply start fresh with PostgreSQL and populate with test data
docker-compose --profile postgres up -d
docker-compose --profile postgres run --rm populate-db-postgres
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

# Count records
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM topics;
SELECT COUNT(*) FROM votes;
```

### 2. Test Application Endpoints

```bash
# Health check (PostgreSQL app runs on port 8001)
curl http://localhost:8001/

# API docs (should work)
open http://localhost:8001/docs

# Register a test user
curl -X POST "http://localhost:8001/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# List topics
curl http://localhost:8001/topics
```

### 3. Performance Comparison

```bash
# Time SQLite queries
time curl -s http://localhost:8000/topics > /dev/null

# Time PostgreSQL queries  
time curl -s http://localhost:8001/topics > /dev/null
```

## 🚨 Common Issues & Solutions

### Issue 1: JSON Column Compatibility
**Problem**: SQLite and PostgreSQL handle JSON differently.

**Solution**: Our models already use `Column(JSON)` which works with both. No changes needed.

### Issue 2: Boolean Column Defaults
**Problem**: SQLite uses 0/1 for booleans, PostgreSQL uses true/false.

**Solution**: SQLAlchemy handles this automatically. No changes needed.

### Issue 3: String Length Specifications
**Problem**: PostgreSQL prefers explicit string lengths for performance.

**Solution**: Already updated in our models:
- `username`: `String(50)`
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

## 📈 Production Deployment Checklist

- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Set unique `SECRET_KEY`
- [ ] Configure firewall (close port 5432 to external access)
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Monitor connection pool usage
- [ ] Set up health checks
- [ ] Configure environment variables
- [ ] Test failover procedures
- [ ] Document recovery procedures

## 🔄 Rolling Back to SQLite

If you need to roll back:

```bash
# Stop PostgreSQL setup
docker-compose --profile postgres down

# Start SQLite setup
docker-compose up -d

# Your SQLite data is preserved in the democrasite_db volume
```

## 📚 Further Reading

- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [SQLAlchemy PostgreSQL Dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [Docker PostgreSQL Best Practices](https://github.com/docker-library/docs/blob/master/postgres/README.md)