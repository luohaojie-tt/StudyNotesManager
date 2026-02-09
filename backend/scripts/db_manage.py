"""Database management utility script."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic.config import Config
from alembic import command
from sqlalchemy import text
from app.core.database import engine, Base, AsyncSessionLocal
from app.models import *  # noqa: F401, F403
from app.core.config import get_settings

settings = get_settings()


async def create_database():
    """Create database if it doesn't exist."""
    from sqlalchemy.ext.asyncio import create_async_engine

    # Connect to default postgres database to create our database
    default_db_url = settings.DATABASE_URL_SYNC.rsplit('/', 1)[0] + '/postgres'
    engine = create_async_engine(default_db_url, isolation_level="AUTOCOMMIT")

    async with engine.connect() as conn:
        result = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname='{settings.DATABASE_URL_SYNC.rsplit('/', 1)[1]}'")
        )
        exists = result.scalar()

        if not exists:
            await conn.execute(text(f"CREATE DATABASE {settings.DATABASE_URL_SYNC.rsplit('/', 1)[1]}"))
            print(f"✅ Database created: {settings.DATABASE_URL_SYNC.rsplit('/', 1)[1]}")
        else:
            print(f"ℹ️  Database already exists: {settings.DATABASE_URL_SYNC.rsplit('/', 1)[1]}")

    await engine.dispose()


async def drop_database():
    """Drop database (USE WITH CAUTION!)."""
    import input

    confirm = input(f"⚠️  Are you sure you want to drop database {settings.DATABASE_URL_SYNC.rsplit('/', 1)[1]}? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Aborted.")
        return

    from sqlalchemy.ext.asyncio import create_async_engine

    # Connect to default postgres database
    default_db_url = settings.DATABASE_URL_SYNC.rsplit('/', 1)[0] + '/postgres'
    engine = create_async_engine(default_db_url, isolation_level="AUTOCOMMIT")

    async with engine.connect() as conn:
        # Terminate all connections to the database
        await conn.execute(text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{settings.DATABASE_URL_SYNC.rsplit('/', 1)[1]}'
            AND pid <> pg_backend_pid();
        """))
        # Drop database
        await conn.execute(text(f"DROP DATABASE {settings.DATABASE_URL_SYNC.rsplit('/', 1)[1]}"))
        print(f"✅ Database dropped: {settings.DATABASE_URL_SYNC.rsplit('/', 1)[1]}")

    await engine.dispose()


async def create_tables():
    """Create all tables directly (without Alembic)."""
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables created successfully")


async def drop_tables():
    """Drop all tables (USE WITH CAUTION!)."""
    import input

    confirm = input("⚠️  Are you sure you want to drop all tables? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Aborted.")
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("✅ All tables dropped")


async def reset_database():
    """Reset database: drop and recreate all tables."""
    await drop_tables()
    await create_tables()


def alembic_upgrade(revision: str = 'head'):
    """Run Alembic upgrade migrations."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, revision)
    print(f"✅ Migrated to {revision}")


def alembic_downgrade(revision: str = '-1'):
    """Run Alembic downgrade migrations."""
    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, revision)
    print(f"✅ Downgraded to {revision}")


def alembic_revision(message: str):
    """Create new Alembic migration."""
    alembic_cfg = Config("alembic.ini")
    command.revision(alembic_cfg, message=message, autogenerate=True)
    print(f"✅ Created migration: {message}")


async def show_schema():
    """Display current database schema."""
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """))
        tables = result.scalars().all()

        print("\n📊 Database Schema:")
        print("=" * 50)
        for table in tables:
            print(f"  • {table}")

            # Show columns
            columns = await conn.execute(text(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position;
            """))
            for col in columns:
                nullable = "NULL" if col.is_nullable == "YES" else "NOT NULL"
                default = f" DEFAULT {col.column_default}" if col.column_default else ""
                print(f"    - {col.column_name}: {col.data_type} {nullable}{default}")
            print()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Database management utility")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Subcommands
    subparsers.add_parser('create-db', help='Create database')
    subparsers.add_parser('drop-db', help='Drop database (CAUTION!)')
    subparsers.add_parser('create-tables', help='Create all tables')
    subparsers.add_parser('drop-tables', help='Drop all tables (CAUTION!)')
    subparsers.add_parser('reset', help='Reset database (drop and recreate)')
    subparsers.add_parser('upgrade', help='Run Alembic upgrade migrations')
    subparsers.add_parser('downgrade', help='Run Alembic downgrade migrations')
    subparsers.add_parser('schema', help='Show database schema')

    # Revision subcommand
    revision_parser = subparsers.add_parser('revision', help='Create new migration')
    revision_parser.add_argument('-m', '--message', required=True, help='Migration message')

    # Optional revision argument for upgrade/downgrade
    parser.add_argument('--revision', help='Revision to upgrade/downgrade to')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    if args.command == 'create-db':
        await create_database()
    elif args.command == 'drop-db':
        await drop_database()
    elif args.command == 'create-tables':
        await create_tables()
    elif args.command == 'drop-tables':
        await drop_tables()
    elif args.command == 'reset':
        await reset_database()
    elif args.command == 'upgrade':
        alembic_upgrade(args.revision or 'head')
    elif args.command == 'downgrade':
        alembic_downgrade(args.revision or '-1')
    elif args.command == 'revision':
        alembic_revision(args.message)
    elif args.command == 'schema':
        await show_schema()


if __name__ == '__main__':
    asyncio.run(main())
