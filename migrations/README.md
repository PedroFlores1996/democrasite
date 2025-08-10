# Database Migrations

This directory contains Alembic database migrations for Democrasite.

## Quick Start

**Important**: Run all alembic commands from the project root directory (where alembic.ini is located).

### Generate a New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new column to users table"

# Create empty migration (for data migrations or custom changes)
alembic revision -m "Update existing data format"
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply migrations up to a specific revision
alembic upgrade ae1027a6acf

# Downgrade to previous migration
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade ae1027a6acf
```

### Check Migration Status

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

## Environment-Specific Usage

### Development (SQLite)
```bash
# Default behavior - uses SQLite database
alembic upgrade head
```

### Production (PostgreSQL)
```bash
# Set PostgreSQL environment variables
export DATABASE_URL="postgresql://user:pass@localhost/democrasite_db"
alembic upgrade head
```

### Docker Environments
```bash
# Development container
docker-compose -f docker/docker-compose.yml exec democrasite alembic upgrade head

# Production container
docker-compose -f docker/docker-compose.yml --profile postgres exec democrasite-postgres alembic upgrade head
```

## Migration Best Practices

### 1. Always Review Generated Migrations
- Check auto-generated migrations before applying
- Ensure data integrity operations are included
- Add custom data transformations if needed

### 2. Test Migrations Thoroughly
```bash
# Test on a copy of production data
alembic upgrade head
alembic downgrade -1  # Test rollback
alembic upgrade head  # Test re-application
```

### 3. Backup Before Production Migrations
```bash
# PostgreSQL backup
docker-compose --profile postgres exec postgres pg_dump -U democrasite_user democrasite_db > backup.sql

# SQLite backup
cp democrasite.db democrasite_backup.db
```

### 4. Migration Naming Conventions
- Use descriptive names: `add_email_verification_to_users`
- Include ticket numbers: `issue_123_add_pending_registrations_table`
- Use verb-noun format: `create_user_preferences_table`

## Common Migration Patterns

### Adding a New Column
```python
def upgrade():
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))

def downgrade():
    op.drop_column('users', 'phone_number')
```

### Adding a New Table
```python
def upgrade():
    op.create_table('user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('preference_key', sa.String(100), nullable=False),
        sa.Column('preference_value', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('user_preferences')
```

### Data Migrations
```python
def upgrade():
    # First alter the schema
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True))
    
    # Then update existing data
    connection = op.get_bind()
    connection.execute(
        text("UPDATE users SET email_verified = true WHERE created_at < :cutoff_date"),
        {"cutoff_date": datetime(2024, 1, 1)}
    )
    
    # Finally apply constraints
    op.alter_column('users', 'email_verified', nullable=False)

def downgrade():
    op.drop_column('users', 'email_verified')
```

## Troubleshooting

### Migration Conflicts
```bash
# If multiple developers created migrations simultaneously
alembic merge heads -m "Merge migrations"
```

### Reset Migration History (Development Only)
```bash
# DANGER: This destroys migration history
rm migrations/versions/*.py
alembic revision --autogenerate -m "Initial migration"
```

### Manual Migration State Management
```bash
# Mark migration as applied without running it
alembic stamp head

# Mark specific revision as current
alembic stamp ae1027a6acf
```

## Integration with Application

The migration system is integrated with your application settings:
- Database URL is automatically loaded from `app.config.settings`
- Works with both SQLite (development) and PostgreSQL (production)
- Supports environment-specific configurations

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Database Migrations
  run: |
    alembic upgrade head
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

### Docker Deployment
```bash
# Apply migrations during container startup
docker-compose -f docker/docker-compose.yml --profile postgres run --rm democrasite-postgres alembic upgrade head
docker-compose --profile postgres up -d
```