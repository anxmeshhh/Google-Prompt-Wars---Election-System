"""
ElectaVerse — MySQL Connection Pool
Provides a thread-safe connection pool for all database operations.
Uses PyMySQL instead of mysql-connector because PyMySQL is pure Python, 
meaning it perfectly integrates with eventlet's monkey patching to achieve 
true non-blocking concurrency without deadlocking native threads.
"""

import pymysql
import pymysql.cursors
import queue
import time
import logging
from config import Config

logger = logging.getLogger('electaverse.db')

class Database:
    """MySQL connection pool manager using PyMySQL and greenlet-safe queue."""

    _pool = None

    @classmethod
    def initialize(cls):
        """Create the connection pool. Retries up to 10 times for Docker startup."""
        if cls._pool is not None:
            return

        for attempt in range(1, 11):
            try:
                # Test connection first
                conn = cls._create_connection()
                conn.close()
                
                # Initialize pool (eventlet monkey patches queue.Queue to be greenlet safe)
                cls._pool = queue.Queue(maxsize=32)
                for _ in range(32):
                    cls._pool.put(cls._create_connection())
                    
                logger.info(f'Database pool created (attempt {attempt})')
                return
            except Exception as e:
                logger.warning(f'DB connect attempt {attempt}/10 failed: {e}')
                if attempt < 10:
                    time.sleep(3)
                else:
                    raise

    @classmethod
    def _create_connection(cls):
        """Create a single PyMySQL connection."""
        return pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            autocommit=True,
            charset='utf8mb4'
        )

    @classmethod
    def get_connection(cls):
        """Get a connection from the pool."""
        if cls._pool is None:
            cls.initialize()
        try:
            # Get connection, wait up to 5 seconds
            conn = cls._pool.get(timeout=5)
            # Ping to check if it's alive, reconnect if dead
            try:
                conn.ping(reconnect=True)
            except Exception:
                conn = cls._create_connection()
            return conn
        except queue.Empty:
            raise Exception("Database connection pool exhausted")

    @classmethod
    def return_connection(cls, conn):
        """Return a connection to the pool."""
        if cls._pool is None:
            conn.close()
            return
        try:
            cls._pool.put_nowait(conn)
        except queue.Full:
            conn.close()

    @classmethod
    def execute(cls, query: str, params: tuple = None) -> list:
        """Execute a SELECT query and return all rows as dicts."""
        conn = cls.get_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()
        finally:
            cls.return_connection(conn)

    @classmethod
    def execute_one(cls, query: str, params: tuple = None) -> dict | None:
        """Execute a SELECT query and return one row as dict."""
        conn = cls.get_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchone()
        finally:
            cls.return_connection(conn)

    @classmethod
    def execute_write(cls, query: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE and return affected rows."""
        conn = cls.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.rowcount
        finally:
            cls.return_connection(conn)

    @classmethod
    def execute_insert(cls, query: str, params: tuple = None) -> int:
        """Execute an INSERT and return the last inserted ID."""
        conn = cls.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.lastrowid
        finally:
            cls.return_connection(conn)

    @classmethod
    def execute_many(cls, query: str, params_list: list) -> int:
        """Execute a batch INSERT/UPDATE."""
        conn = cls.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
        finally:
            cls.return_connection(conn)

    @classmethod
    def execute_script(cls, script: str):
        """Execute a multi-statement SQL script (e.g., schema)."""
        conn = cls.get_connection()
        try:
            with conn.cursor() as cursor:
                for statement in script.split(';'):
                    stmt = statement.strip()
                    if stmt:
                        cursor.execute(stmt)
                conn.commit()
        finally:
            cls.return_connection(conn)
