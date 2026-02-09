# Database Migration Guide

## Quick Start

### 1. Setup Database Connection

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your database credentials
# DATABASE_URL_SYNC=postgresql://user:password@localhost:5432/studynotes
```

### 2. Create Database

```bash
# Using the utility script
python scripts/db_manage.py create-db

# Or manually with psql
psql -U postgres
CREATE DATABASE studynotes;
\q
```

### 3. Install pgvector Extension

```bash
# On Ubuntu/Debian
git clone --branch v0.5.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# On macOS with Homebrew
brew install pgvector

# Verify installation
psql -U postgres -d studynotes -c "CREATE EXTENSION vector;"
```

### 4. Run Migrations

```bash
# Using the utility script
python scripts/db_manage.py upgrade

# Or using Alembic directly
alembic upgrade head
```

### 5. Verify Installation

```bash
# Show database schema
python scripts/db_manage.py schema

# Or with psql
psql -U postgres -d studynotes
\dt
\dx
```

## Migration Workflow

### Creating New Migrations

```bash
# Using utility script
python scripts/db_manage.py revision -m "Add user preferences table"

# Or using Alembic directly
alembic revision --autogenerate -m "Add user preferences table"
```

### Applying Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Show migration history
alembic history

# Show current version
alembic current
```

### Rolling Back Migrations

```bash
# Rollback one step
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback to base (no tables)
alembic downgrade base
```

## Common Tasks

### Add a New Column

```bash
# 1. Create migration
alembic revision -m "Add phone column to users"

# 2. Edit the generated migration file to add:
# op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))

# 3. Apply migration
alembic upgrade head
```

### Create a New Table

```bash
# 1. Create the model in app/models/

# 2. Generate migration
alembic revision --autogenerate -m "Add user_preferences table"

# 3. Review the generated migration
# 4. Apply migration
alembic upgrade head
```

### Add an Index

```python
# In your migration file:
op.create_index(
    'idx_users_email',
    'users',
    ['email']
)

# For vector similarity search:
op.execute('''
    CREATE INDEX idx_notes_embedding
    ON notes USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
''')
```

### Add Foreign Key

```python
# In your migration file:
op.add_column(
    'notes',
    sa.Column('user_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('users.id', ondelete='CASCADE'))
)
```

## Database Management Commands

### Using Utility Script

```bash
# Show help
python scripts/db_manage.py --help

# Create database
python scripts/db_manage.py create-db

# Drop database (CAUTION!)
python scripts/db_manage.py drop-db

# Create tables directly
python scripts/db_manage.py create-tables

# Drop tables (CAUTION!)
python scripts/db_manage.py drop-tables

# Reset database (drop and recreate)
python scripts/db_manage.py reset

# Show schema
python scripts/db_manage.py schema
```

### Using psql

```bash
# Connect to database
psql -U postgres -d studynotes

# List tables
\dt

# Describe table
\d notes

# Show indexes
\di

# Show extensions
\dx

# Execute query
SELECT COUNT(*) FROM users;

# Export schema
pg_dump -U postgres -s studynotes > schema.sql

# Import schema
psql -U postgres studynotes < schema.sql

# Quit
\q
```

## Troubleshooting

### Migration Conflicts

```bash
# If autogenerate detects changes that don't exist
alembic stamp head

# If you need to reset
alembic downgrade base
alembic upgrade head
```

### Foreign Key Issues

If you get foreign key constraint errors during migration:

1. Check the order of table creation
2. Ensure referenced tables are created first
3. Use `ondelete='CASCADE'` appropriately

### pgvector Extension Not Found

```sql
-- Check if extension is installed
SELECT * FROM pg_available_extensions WHERE name = 'vector';

-- Install extension
CREATE EXTENSION IF NOT EXISTS vector;

-- If extension is not available, install pgvector:
-- Ubuntu/Debian: see instructions above
-- macOS: brew install pgvector
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
pg_isready

# Check connection
psql -U postgres -d studynotes

# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql-15-main.log
```

### Permission Issues

```sql
-- Grant privileges to user
GRANT ALL PRIVILEGES ON DATABASE studynotes TO studynotes_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO studynotes_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO studynotes_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO studynotes_user;

-- Grant usage on extensions
GRANT USAGE ON SCHEMA public TO studynotes_user;
```

## Best Practices

1. **Always review** auto-generated migrations before applying
2. **Test migrations** on development database first
3. **Backup database** before running major migrations
4. **Use descriptive messages** for migrations
5. **Keep migrations reversible** (implement both upgrade and downgrade)
6. **Avoid data loss** in downgrade operations when possible
7. **Version control** your migration files
8. **Document breaking changes** in migration descriptions

## Production Checklist

Before running migrations in production:

- [ ] Database backup created
- [ ] Migration tested in staging
- [ ] Maintenance window scheduled
- [ ] Rollback plan prepared
- [ ] Team notified
- [ ] Monitoring enabled
- [ ] Performance tested with production data size

## Performance Considerations

### For Large Tables

```bash
# Add column without default value (fast)
ALTER TABLE notes ADD COLUMN new_column TEXT;

# Add default value (slow, locks table)
ALTER TABLE notes ALTER COLUMN new_column SET DEFAULT 'default_value';

# Better approach for large tables:
-- 1. Add column without default
-- 2. Update rows in batches
-- 3. Set default for new rows
-- 4. Add constraint
```

### Index Creation

```sql
-- Create index concurrently (doesn't block writes)
CREATE INDEX CONCURRENTLY idx_notes_user
ON notes(user_id, created_at DESC);
```

## Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [SQLAlchemy 2.0 Migration Guide](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)
