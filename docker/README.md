# Docker Configuration

This directory contains all Docker-related files for Democrasite.

## Files Overview

- **`docker-compose.yml`** - Multi-environment Docker Compose configuration
- **`Dockerfile`** - Application container build instructions
- **`.dockerignore`** - Files excluded from Docker build context

## Quick Start

### Development Environment (SQLite)
```bash
# From project root
docker-compose -f docker/docker-compose.yml up -d

# Populate with test data
docker-compose -f docker/docker-compose.yml run --rm populate-db

# Access at http://localhost:8000
```

### Production Environment (PostgreSQL)
```bash
# From project root
docker-compose -f docker/docker-compose.yml --profile postgres up -d

# Populate with test data
docker-compose -f docker/docker-compose.yml --profile postgres run --rm populate-db-postgres

# Access at http://localhost:8001
```

## Environment Profiles

### Default Profile (Development)
- **Database**: SQLite
- **Port**: 8000
- **Email Verification**: Disabled
- **Use Case**: Local development, testing

### Postgres Profile (Production)
- **Database**: PostgreSQL
- **Port**: 8001 
- **Email Verification**: Enabled
- **Use Case**: Production deployment, integration testing

## Environment Variables

Create a `.env` file in the project root for production:

```env
# Database
POSTGRES_USER=democrasite_user
POSTGRES_PASSWORD=your-secure-password

# Application
SECRET_KEY=your-jwt-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (Production)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@democrasite.com
FRONTEND_URL=http://localhost:8001
```

## Common Commands

### Container Management
```bash
# Start services
docker-compose -f docker/docker-compose.yml up -d

# Stop services
docker-compose -f docker/docker-compose.yml down

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Rebuild containers
docker-compose -f docker/docker-compose.yml build --no-cache
```

### Database Operations
```bash
# Apply migrations (development)
docker-compose -f docker/docker-compose.yml exec democrasite alembic upgrade head

# Apply migrations (production)
docker-compose -f docker/docker-compose.yml --profile postgres exec democrasite-postgres alembic upgrade head

# Access PostgreSQL directly
docker-compose -f docker/docker-compose.yml --profile postgres exec postgres psql -U democrasite_user -d democrasite_db
```

### Development Helpers
```bash
# Run tests
docker-compose -f docker/docker-compose.yml exec democrasite python -m pytest tests/ -v

# Access container shell
docker-compose -f docker/docker-compose.yml exec democrasite bash
```

## Container Architecture

### Services

1. **democrasite** (Development)
   - Built from `Dockerfile`
   - SQLite database
   - Port 8000
   - Volume: `democrasite_db`

2. **postgres** (Production)
   - PostgreSQL 15 Alpine
   - Port 5432
   - Volume: `postgres_data`
   - Profile: `postgres`

3. **democrasite-postgres** (Production)
   - Built from `Dockerfile`
   - Connects to PostgreSQL
   - Port 8001
   - Profile: `postgres`

4. **populate-db** utilities
   - One-time containers for data population
   - Separate variants for SQLite and PostgreSQL

### Volumes

- **`democrasite_db`**: SQLite database storage (development)
- **`postgres_data`**: PostgreSQL database storage (production)

### Networks

- **`default`**: Development environment
- **`democrasite-network`**: Production environment isolation

## Health Checks

All services include health checks:
- **Applications**: HTTP requests to root endpoint
- **PostgreSQL**: `pg_isready` command
- **Intervals**: 30s for apps, 10s for database
- **Startup grace period**: 40s for apps

## Troubleshooting

### Port Conflicts
If ports 8000/8001 are in use:
```bash
# Find processes using the ports
lsof -i :8000
lsof -i :8001

# Kill if needed
kill $(lsof -t -i:8000)
```

### Volume Issues
```bash
# Remove all volumes (WARNING: destroys data)
docker-compose -f docker/docker-compose.yml down --volumes

# Remove specific volume
docker volume rm democrasite_postgres_data
```

### Container Rebuild
```bash
# Force rebuild without cache
docker-compose -f docker/docker-compose.yml build --no-cache --pull
```

## Production Deployment

For production deployment:

1. **Security**: Use strong passwords and secrets
2. **Networking**: Configure reverse proxy (nginx)
3. **SSL**: Set up HTTPS certificates
4. **Monitoring**: Add logging and metrics
5. **Backups**: Implement database backup strategy
6. **Updates**: Plan for zero-downtime deployments

See [`POSTGRESQL_SETUP.md`](../POSTGRESQL_SETUP.md) for detailed setup and testing procedures.