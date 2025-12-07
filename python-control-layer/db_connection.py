"""Database connection and configuration for TimescaleDB"""
import os
import logging
from contextlib import contextmanager
from typing import Optional
import psycopg2
import psycopg2.pool as pool
from secrets_manager import get_secrets_manager

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration"""
    
    def __init__(self):
        """Initialize database configuration from secrets manager"""
        secrets = get_secrets_manager()
        db_creds = secrets.get_database_credentials()
        
        self.HOST = db_creds.get('host', 'localhost')
        self.PORT = int(db_creds.get('port', '5432'))
        self.DATABASE = db_creds.get('database', 'modax')
        self.USER = db_creds.get('user', 'modax_user')
        self.PASSWORD = db_creds.get('password', '')
        self.MIN_CONNECTIONS = int(os.getenv("DB_POOL_MIN", "2"))
        self.MAX_CONNECTIONS = int(os.getenv("DB_POOL_MAX", "10"))
        
        # Check if database is enabled
        self.ENABLED = os.getenv("DB_ENABLED", "false").lower() == "true"


class DatabaseConnectionPool:
    """Database connection pool manager"""
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize database connection pool
        
        Args:
            config: Database configuration
        """
        self.config = config
        self.pool: Optional[pool.ThreadedConnectionPool] = None
        
        if config.ENABLED:
            self.initialize_pool()
    
    def initialize_pool(self):
        """Initialize the connection pool"""
        try:
            self.pool = pool.ThreadedConnectionPool(
                self.config.MIN_CONNECTIONS,
                self.config.MAX_CONNECTIONS,
                host=self.config.HOST,
                port=self.config.PORT,
                database=self.config.DATABASE,
                user=self.config.USER,
                password=self.config.PASSWORD
            )
            logger.info(
                f"Database connection pool initialized "
                f"({self.config.MIN_CONNECTIONS}-{self.config.MAX_CONNECTIONS} connections)"
            )
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Get a database connection from the pool
        
        Yields:
            Database connection
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, commit: bool = False):
        """
        Get a database cursor
        
        Args:
            commit: Whether to commit after execution
            
        Yields:
            Database cursor
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def close(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")
    
    def is_available(self) -> bool:
        """Check if database is available"""
        if not self.pool:
            return False
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database availability check failed: {e}")
            return False


# Global database connection pool instance
_db_pool: Optional[DatabaseConnectionPool] = None


def get_db_pool() -> DatabaseConnectionPool:
    """Get or create the global database connection pool"""
    global _db_pool
    if _db_pool is None:
        config = DatabaseConfig()
        _db_pool = DatabaseConnectionPool(config)
    return _db_pool


def set_db_pool(db_pool: DatabaseConnectionPool):
    """Set a custom database connection pool (for testing)"""
    global _db_pool
    _db_pool = db_pool


def close_db_pool():
    """Close the global database connection pool"""
    global _db_pool
    if _db_pool:
        _db_pool.close()
        _db_pool = None
