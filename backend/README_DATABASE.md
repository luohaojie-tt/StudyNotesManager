# Database Setup Guide

## Prerequisites

1. **PostgreSQL 15+** with pgvector extension
2. **Python 3.11+**
3. **pip** package manager

## Installation Steps

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE studynotes;

# Create user (optional, if you want a dedicated user)
CREATE USER studynotes_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE studynotes TO studynotes_user;

\q
```

### 4. Install pgvector Extension

```bash
# Install pgvector (Linux)
git clone --branch v0.5.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
# sudo make install PG_CONFIG=/usr/local/pgsql/bin/pg_config

# Or on macOS with Homebrew
brew install pgvector
```

### 5. Run Database Migrations

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Generate initial migration
alembic revision --autogenerate -m "Initial schema with all core tables"

# Apply migration
alembic upgrade head
```

### 6. Verify Database Schema

```bash
# Connect to database
psql -U postgres -d studynotes

# List all tables
\dt

# Check pgvector extension
\dx

# Describe a specific table
\d notes

# Exit
\q
```

## Database Schema

### Core Tables

1. **users** - User accounts and authentication
2. **notes** - User notes with OCR and vector embeddings
3. **mindmaps** - AI-generated mind maps
4. **mindmap_knowledge_points** - Knowledge points from mind maps
5. **quiz_questions** - Quiz questions for testing
6. **user_quiz_records** - User quiz attempt records
7. **mistakes** - Wrong answers notebook
8. **mistake_reviews** - Review records for spaced repetition
9. **categories** - Note categories with hierarchy
10. **category_relations** - Category relationships
11. **note_shares** - Note sharing configuration
12. **study_sessions** - Study session tracking

### Key Features

- **Vector Search**: pgvector for semantic search on notes and knowledge points
- **Hierarchical Categories**: Support for nested category structures
- **Version Control**: Mindmap versioning and comparison
- **Spaced Repetition**: Ebbinghaus forgetting curve implementation
- **Full-text Search**: Optimized indexes for content search

## Migration Commands

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# View migration history
alembic history

# View current version
alembic current

# Reset database (DROP ALL TABLES)
alembic downgrade base
```

## Database Backup and Restore

### Backup

```bash
# Full backup
pg_dump -U postgres studynotes > backup_$(date +%Y%m%d).sql

# Schema only
pg_dump -U postgres -s studynotes > schema_$(date +%Y%m%d).sql

# Data only
pg_dump -U postgres -a studynotes > data_$(date +%Y%m%d).sql
```

### Restore

```bash
# Restore from backup
psql -U postgres studynotes < backup_20240101.sql
```

## Performance Tuning

### Indexes

All frequently queried columns have indexes:
- Foreign keys
- Timestamp fields (created_at, updated_at)
- Vector embeddings (ivfflat for similarity search)
- Unique constraints (email, share_id)

### Connection Pooling

Configured in `app/core/database.py`:
- Pool size: 10
- Max overflow: 20
- Pool pre-ping enabled

### Query Optimization

- Use `EXPLAIN ANALYZE` to analyze slow queries
- Monitor with `pg_stat_statements`
- Consider materialized views for complex aggregations

## Troubleshooting

### pgvector Extension Not Found

```sql
-- Check if extension exists
SELECT * FROM pg_available_extensions WHERE name = 'vector';

-- Install if missing
CREATE EXTENSION IF NOT EXISTS vector;
```

### Migration Conflicts

```bash
# Stamp current database version
alembic stamp head

# Or reset to base
alembic stamp base
```

### Connection Issues

Check `DATABASE_URL` in `.env`:
- Format: `postgresql://user:password@host:port/database`
- Ensure PostgreSQL is running: `pg_isready`
- Check firewall/network settings

## Security Best Practices

1. **Never commit .env file** to version control
2. **Use strong passwords** for database users
3. **Limit database user permissions** (use dedicated user, not postgres)
4. **Enable SSL** for production connections
5. **Regular backups** with automated scheduling
6. **Monitor slow queries** and suspicious activity
7. **Keep PostgreSQL updated** with security patches

## ER Diagram

For a visual representation of the database schema, see:
- `docs/database/er-diagram.png` (generated with draw.io or similar)

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
