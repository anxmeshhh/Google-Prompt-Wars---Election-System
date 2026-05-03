"""
ElectaVerse — MySQL Connection Pool
Provides a thread-safe connection pool for all database operations.
"""

import mysql.connector
from mysql.connector import pooling
from config import Config


class Database:
    """MySQL connection pool manager."""

    _pool = None

    @classmethod
    def initialize(cls):
        """Create the connection pool. Retries up to 10 times for Docker startup."""
        if cls._pool is not None:
            return
        import time
        import logging
        logger = logging.getLogger('electaverse.db')
        for attempt in range(1, 11):
            try:
                cls._pool = pooling.MySQLConnectionPool(
                    pool_name='electaverse_pool',
                    pool_size=32,
                    pool_reset_session=True,
                    host=Config.DB_HOST,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME,
                    autocommit=True,
                )
                logger.info(f'Database pool created (attempt {attempt})')
                return
            except Exception as e:
                logger.warning(f'DB connect attempt {attempt}/10 failed: {e}')
                if attempt < 10:
                    time.sleep(3)
                else:
                    raise

    @classmethod
    def get_connection(cls):
        """Get a connection from the pool."""
        if cls._pool is None:
            cls.initialize()
        return cls._pool.get_connection()

    @classmethod
    def execute(cls, query: str, params: tuple = None) -> list:
        """Execute a SELECT query and return all rows as dicts."""
        def _run():
            conn = cls.get_connection()
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                cursor.close()
                return results
            finally:
                conn.close()
        
        try:
            import eventlet.tpool
            return eventlet.tpool.execute(_run)
        except (ImportError, RuntimeError):
            return _run()

    @classmethod
    def execute_one(cls, query: str, params: tuple = None) -> dict | None:
        """Execute a SELECT query and return one row as dict."""
        def _run():
            conn = cls.get_connection()
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params or ())
                result = cursor.fetchone()
                cursor.close()
                return result
            finally:
                conn.close()
                
        try:
            import eventlet.tpool
            return eventlet.tpool.execute(_run)
        except (ImportError, RuntimeError):
            return _run()

    @classmethod
    def execute_write(cls, query: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE and return affected rows."""
        def _run():
            conn = cls.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                conn.commit()
                affected = cursor.rowcount
                cursor.close()
                return affected
            finally:
                conn.close()
                
        try:
            import eventlet.tpool
            return eventlet.tpool.execute(_run)
        except (ImportError, RuntimeError):
            return _run()

    @classmethod
    def execute_insert(cls, query: str, params: tuple = None) -> int:
        """Execute an INSERT and return the last inserted ID."""
        def _run():
            conn = cls.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                conn.commit()
                last_id = cursor.lastrowid
                cursor.close()
                return last_id
            finally:
                conn.close()
                
        try:
            import eventlet.tpool
            return eventlet.tpool.execute(_run)
        except (ImportError, RuntimeError):
            return _run()

    @classmethod
    def execute_many(cls, query: str, params_list: list) -> int:
        """Execute a batch INSERT/UPDATE."""
        def _run():
            conn = cls.get_connection()
            try:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                affected = cursor.rowcount
                cursor.close()
                return affected
            finally:
                conn.close()
                
        try:
            import eventlet.tpool
            return eventlet.tpool.execute(_run)
        except (ImportError, RuntimeError):
            return _run()

    @classmethod
    def execute_script(cls, script: str):
        """Execute a multi-statement SQL script (e.g., schema)."""
        def _run():
            conn = cls.get_connection()
            try:
                cursor = conn.cursor()
                for statement in script.split(';'):
                    stmt = statement.strip()
                    if stmt:
                        cursor.execute(stmt)
                conn.commit()
                cursor.close()
            finally:
                conn.close()
                
        try:
            import eventlet.tpool
            eventlet.tpool.execute(_run)
        except (ImportError, RuntimeError):
            _run()
