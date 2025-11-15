#!/usr/bin/env python3
"""
Database Setup Script for FARS Multi-Sensory Database

This script:
1. Creates the PostgreSQL database (if it doesn't exist)
2. Enables PostGIS extension
3. Creates all tables from schema.sql
4. Creates views from create_views.sql
5. Verifies the setup

Usage:
    python scripts/01_setup_database.py

    # With custom config:
    python scripts/01_setup_database.py --config /path/to/database.yaml

    # Drop existing database (CAUTION!):
    python scripts/01_setup_database.py --drop-existing
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import yaml
from loguru import logger


def load_config(config_path: str) -> dict:
    """Load database configuration"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['database']


def create_database(config: dict, drop_existing: bool = False):
    """Create the database if it doesn't exist"""
    db_name = config['database']

    # Connect to PostgreSQL server (postgres database)
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cursor.fetchone()

        if exists:
            if drop_existing:
                logger.warning(f"Dropping existing database: {db_name}")
                # Terminate existing connections
                cursor.execute(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{db_name}'
                    AND pid <> pg_backend_pid();
                """)
                cursor.execute(f'DROP DATABASE {db_name}')
                logger.info(f"Database {db_name} dropped")
            else:
                logger.info(f"Database {db_name} already exists")
                cursor.close()
                conn.close()
                return False

        # Create database
        cursor.execute(f'CREATE DATABASE {db_name}')
        logger.info(f"Database {db_name} created successfully")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise


def enable_postgis(config: dict):
    """Enable PostGIS extension"""
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        cursor = conn.cursor()

        # Enable PostGIS
        cursor.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
        conn.commit()

        # Verify PostGIS version
        cursor.execute('SELECT PostGIS_version();')
        version = cursor.fetchone()[0]
        logger.info(f"PostGIS enabled: {version}")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error enabling PostGIS: {e}")
        raise


def execute_sql_file(config: dict, sql_file: Path):
    """Execute SQL commands from a file"""
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        cursor = conn.cursor()

        # Read and execute SQL file
        with open(sql_file, 'r') as f:
            sql = f.read()

        cursor.execute(sql)
        conn.commit()

        logger.info(f"Executed SQL file: {sql_file.name}")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error executing SQL file {sql_file}: {e}")
        raise


def verify_setup(config: dict):
    """Verify database setup"""
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        cursor = conn.cursor()

        # Count tables
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE';
        """)
        table_count = cursor.fetchone()[0]

        # Count views
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.views
            WHERE table_schema = 'public';
        """)
        view_count = cursor.fetchone()[0]

        # List tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]

        logger.info(f"✓ Setup verified:")
        logger.info(f"  - Tables: {table_count}")
        logger.info(f"  - Views: {view_count}")
        logger.info(f"  - Table list: {', '.join(tables[:10])}...")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        logger.error(f"Error verifying setup: {e}")
        return False


def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(
        description='Setup FARS Multi-Sensory Database'
    )
    parser.add_argument(
        '--config',
        default='config/database.yaml',
        help='Path to database config file'
    )
    parser.add_argument(
        '--drop-existing',
        action='store_true',
        help='Drop existing database before creating (CAUTION!)'
    )
    parser.add_argument(
        '--skip-schema',
        action='store_true',
        help='Skip schema creation (database already set up)'
    )
    parser.add_argument(
        '--skip-views',
        action='store_true',
        help='Skip view creation'
    )

    args = parser.parse_args()

    # Setup logging
    logger.add(
        project_root / 'logs' / 'database_setup.log',
        rotation="10 MB",
        level="DEBUG"
    )

    logger.info("=" * 60)
    logger.info("FARS Multi-Sensory Database Setup")
    logger.info("=" * 60)

    # Load configuration
    config_path = project_root / args.config
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        logger.info("Please create config/database.yaml from the template")
        sys.exit(1)

    config = load_config(config_path)
    logger.info(f"Loaded config for database: {config['database']}")

    # Confirm if dropping existing
    if args.drop_existing:
        response = input(
            f"\n⚠️  WARNING: This will DROP the existing database '{config['database']}' "
            f"and ALL data will be lost!\n"
            f"Type 'yes' to confirm: "
        )
        if response.lower() != 'yes':
            logger.info("Aborted by user")
            sys.exit(0)

    # Step 1: Create database
    logger.info("\n[1/5] Creating database...")
    create_database(config, drop_existing=args.drop_existing)

    # Step 2: Enable PostGIS
    logger.info("\n[2/5] Enabling PostGIS extension...")
    enable_postgis(config)

    # Step 3: Create schema
    if not args.skip_schema:
        logger.info("\n[3/5] Creating database schema...")
        schema_file = project_root / 'sql' / 'schema.sql'
        if schema_file.exists():
            execute_sql_file(config, schema_file)
        else:
            logger.warning(f"Schema file not found: {schema_file}")
    else:
        logger.info("\n[3/5] Skipping schema creation")

    # Step 4: Create views
    if not args.skip_views:
        logger.info("\n[4/5] Creating database views...")
        views_file = project_root / 'sql' / 'create_views.sql'
        if views_file.exists():
            execute_sql_file(config, views_file)
        else:
            logger.warning(f"Views file not found: {views_file}")
    else:
        logger.info("\n[4/5] Skipping view creation")

    # Step 5: Verify setup
    logger.info("\n[5/5] Verifying database setup...")
    if verify_setup(config):
        logger.info("\n✓ Database setup completed successfully!")
        logger.info(f"\nYou can now connect to: {config['database']}")
        logger.info(f"Host: {config['host']}:{config['port']}")
        logger.info(f"User: {config['user']}")
    else:
        logger.error("\n✗ Database setup verification failed")
        sys.exit(1)


if __name__ == '__main__':
    # Ensure logs directory exists
    (project_root / 'logs').mkdir(exist_ok=True)
    main()
