"""
Database connection management for FARS Multi-Sensory Database
Provides connection pooling and session management
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from loguru import logger


class Database:
    """
    Database connection manager with connection pooling

    Supports both raw psycopg2 connections and SQLAlchemy ORM
    """

    def __init__(self, config_path: Optional[str] = None, environment: str = 'database'):
        """
        Initialize database connection

        Args:
            config_path: Path to database.yaml config file
            environment: Which config section to use ('database', 'database_dev', 'database_test')
        """
        self.config_path = config_path or self._find_config()
        self.environment = environment
        self.config = self._load_config()

        # Connection pools
        self._pg_pool: Optional[pool.SimpleConnectionPool] = None
        self._engine = None
        self._session_factory = None

        # Initialize connections
        self._init_pg_pool()
        self._init_sqlalchemy()

        logger.info(f"Database connection initialized: {self.config['database']}")

    def _find_config(self) -> str:
        """Find database configuration file"""
        # Try multiple locations
        possible_paths = [
            Path('config/database.yaml'),
            Path('../config/database.yaml'),
            Path('../../config/database.yaml'),
            Path.home() / '.config' / 'fars_multisensory' / 'database.yaml'
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        raise FileNotFoundError(
            "Could not find database.yaml config file. "
            "Please create one in the config/ directory or specify path explicitly."
        )

    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration from YAML"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

            if self.environment not in config:
                raise KeyError(f"Environment '{self.environment}' not found in config")

            db_config = config[self.environment]

            # Allow environment variable overrides
            db_config['password'] = os.getenv('DB_PASSWORD', db_config.get('password'))
            db_config['user'] = os.getenv('DB_USER', db_config.get('user'))
            db_config['host'] = os.getenv('DB_HOST', db_config.get('host'))

            return db_config

        except Exception as e:
            logger.error(f"Failed to load database config: {e}")
            raise

    def _init_pg_pool(self):
        """Initialize psycopg2 connection pool"""
        try:
            pool_config = self.config.get('pool', {})
            min_conn = pool_config.get('min_connections', 2)
            max_conn = pool_config.get('max_connections', 10)

            self._pg_pool = pool.SimpleConnectionPool(
                min_conn,
                max_conn,
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )

            logger.debug(f"Connection pool created: {min_conn}-{max_conn} connections")

        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    def _init_sqlalchemy(self):
        """Initialize SQLAlchemy engine and session factory"""
        try:
            # Create connection string
            conn_str = (
                f"postgresql://{self.config['user']}:{self.config['password']}"
                f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
            )

            # Create engine
            self._engine = create_engine(
                conn_str,
                poolclass=NullPool,  # Use psycopg2 pool instead
                echo=False  # Set to True for SQL debugging
            )

            # Create session factory
            self._session_factory = sessionmaker(bind=self._engine)

            logger.debug("SQLAlchemy engine created")

        except Exception as e:
            logger.error(f"Failed to create SQLAlchemy engine: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """
        Get a psycopg2 connection from the pool

        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM crashes LIMIT 10")
        """
        conn = self._pg_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            self._pg_pool.putconn(conn)

    @contextmanager
    def get_session(self) -> Session:
        """
        Get a SQLAlchemy session

        Usage:
            with db.get_session() as session:
                crashes = session.query(Crash).limit(10).all()
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()

    def execute(self, query: str, params: Optional[tuple] = None) -> list:
        """
        Execute a query and return results

        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)

        Returns:
            List of tuples with query results
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())

            # Try to fetch results (SELECT queries)
            try:
                results = cursor.fetchall()
                cursor.close()
                return results
            except psycopg2.ProgrammingError:
                # No results to fetch (INSERT/UPDATE/DELETE)
                cursor.close()
                return []

    def execute_file(self, sql_file: str):
        """
        Execute SQL commands from a file

        Args:
            sql_file: Path to SQL file
        """
        with open(sql_file, 'r') as f:
            sql = f.read()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            cursor.close()

        logger.info(f"Executed SQL file: {sql_file}")

    def test_connection(self) -> bool:
        """
        Test database connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                cursor.close()
                logger.info(f"Connected to: {version}")
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def close(self):
        """Close all connections"""
        if self._pg_pool:
            self._pg_pool.closeall()
            logger.info("Connection pool closed")

        if self._engine:
            self._engine.dispose()
            logger.info("SQLAlchemy engine disposed")


def get_connection(config_path: Optional[str] = None, environment: str = 'database') -> Database:
    """
    Convenience function to get a database connection

    Args:
        config_path: Path to database.yaml
        environment: Config environment to use

    Returns:
        Database connection object
    """
    return Database(config_path=config_path, environment=environment)


# Example usage
if __name__ == '__main__':
    # Test the database connection
    from loguru import logger

    logger.add("logs/database.log", rotation="10 MB")

    db = Database()

    if db.test_connection():
        print("✓ Database connection successful!")

        # Example query
        result = db.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
        print(f"Number of tables: {result[0][0]}")

    db.close()
