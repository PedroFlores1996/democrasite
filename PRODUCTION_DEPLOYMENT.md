# Production Deployment Guide

This guide covers production deployment, security configuration, and operational procedures for Democrasite using PostgreSQL and email verification.

> **💡 For Development Setup**: See [README.md](./README.md) for local development and Docker setup instructions.

## 🏭 Production Environment Configuration

### Environment Variables

Create a `.env` file for production deployment:

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

# Apply database migrations
docker-compose --profile postgres exec democrasite-postgres alembic upgrade head
```

## 🗄️ Database Management

### Migration Commands

```bash
# Apply all pending migrations
docker-compose --profile postgres exec democrasite-postgres alembic upgrade head

# Check current migration status
docker-compose --profile postgres exec democrasite-postgres alembic current

# View migration history
docker-compose --profile postgres exec democrasite-postgres alembic history

# Check for pending migrations
docker-compose --profile postgres exec democrasite-postgres alembic heads
```

### Direct Database Access

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

## 🔧 Production Configuration

### Connection Pool Settings

For high-traffic production environments, configure connection pooling in `app/db/database.py`:

```python
# Production connection pool configuration
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=settings.DATABASE_CONNECT_ARGS,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300
)
```

### Security Configuration

- **Firewall**: Close port 5432 to external access (database should only be accessible from app container)
- **Strong Passwords**: Use complex passwords for PostgreSQL and JWT secrets
- **SMTP Security**: Use app-specific passwords for email services
- **Environment Variables**: Never commit secrets to version control

## 🔍 Verification & Testing

### Application Health Check

```bash
# Health check (production app runs on port 8001)
curl http://localhost:8001/

# API documentation
curl http://localhost:8001/docs

# Test registration (production mode - requires email verification)
curl -X POST "http://localhost:8001/api/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}'
```

### Staged Registration System Testing

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

### Performance Testing

```bash
# Compare SQLite (development - port 8000) vs PostgreSQL (production - port 8001)
time curl -s http://localhost:8000/api/topics > /dev/null
time curl -s http://localhost:8001/api/topics > /dev/null
```

### Email Verification Testing

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

## 🚨 Troubleshooting

### Common Issues & Solutions

#### Issue 1: JSON Column Compatibility
**Problem**: SQLite and PostgreSQL handle JSON differently.
**Solution**: Our models use `Column(JSON)` which works with both. No changes needed.

#### Issue 2: Boolean Column Defaults
**Problem**: SQLite uses 0/1 for booleans, PostgreSQL uses true/false.
**Solution**: SQLAlchemy handles this automatically. No changes needed.

#### Issue 3: String Length Specifications
**Problem**: PostgreSQL prefers explicit string lengths for performance.
**Solution**: Already configured in our models:
- `username`: `String(50)`
- `email`: `String(255)` 
- `title`: `String(500)`
- `share_code`: `String(8)`
- `choice`: `String(1000)`

#### Issue 4: Connection Pool Exhaustion
**Problem**: PostgreSQL connections may exhaust under load.
**Solution**: Configure connection pooling (see Production Configuration section above).

#### Issue 5: Pending Registrations Table Missing
**Problem**: `relation "pending_registrations" does not exist`
**Solution**: Run migrations to create the table:
```bash
docker-compose --profile postgres exec democrasite-postgres alembic upgrade head
```

#### Issue 6: SMTP Configuration Warnings
**Problem**: Warnings about missing SMTP_USERNAME/SMTP_PASSWORD
**Solution**: Set environment variables or use .env file:
```bash
docker-compose --profile postgres --env-file .env up -d
```

## 📈 Production Deployment Checklist

- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Set unique `SECRET_KEY` (256-bit random string)
- [ ] Configure SMTP credentials for email verification
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Configure firewall (close port 5432 to external access)
- [ ] Set up database backups and retention policy
- [ ] Configure log rotation for application and database logs
- [ ] Monitor connection pool usage and performance metrics
- [ ] Set up health checks and monitoring alerts
- [ ] Test email verification flow end-to-end
- [ ] Test staged registration system with failed emails
- [ ] Document recovery and rollback procedures
- [ ] Configure SSL/TLS certificates for production domain
- [ ] Set up reverse proxy (nginx/Apache) if needed
- [ ] Plan scaling strategy (horizontal/vertical)

## 🔄 Environment Management

### Switch to Production Mode
```bash
# Stop development setup if running
docker-compose down

# Start production setup
docker-compose --profile postgres --env-file .env up -d

# Apply migrations
docker-compose --profile postgres exec democrasite-postgres alembic upgrade head

# Optional: Populate with test data
docker-compose --profile postgres run --rm populate-db-postgres
```

### Switch Back to Development Mode
```bash
# Stop production setup
docker-compose --profile postgres down

# Start development setup
docker-compose up -d

# Your SQLite data is preserved in the democrasite_db volume
```

### Data Migration Between Environments
```bash
# Export data from SQLite (development)
docker-compose exec democrasite python3 -c "
import sqlite3
import json
conn = sqlite3.connect('democrasite.db')
# Custom export script here
"

# Import data to PostgreSQL (production)
# Use appropriate data migration scripts based on your needs
```

## 📊 Monitoring & Maintenance

### Health Monitoring
```bash
# Check container status
docker-compose --profile postgres ps

# View application logs
docker-compose --profile postgres logs -f democrasite-postgres

# View database logs
docker-compose --profile postgres logs -f postgres

# Monitor resource usage
docker stats $(docker-compose --profile postgres ps -q)
```

### Database Maintenance
```bash
# Database size monitoring
docker-compose --profile postgres exec postgres psql -U democrasite_user -d democrasite_db -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Index usage analysis
docker-compose --profile postgres exec postgres psql -U democrasite_user -d democrasite_db -c "
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public'
ORDER BY n_distinct DESC;"
```

## 📚 Additional Resources

- [Database Migrations Guide](./migrations/README.md)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [SQLAlchemy PostgreSQL Dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [Docker PostgreSQL Best Practices](https://github.com/docker-library/docs/blob/master/postgres/README.md)
- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [FastAPI Production Deployment](https://fastapi.tiangolo.com/deployment/)