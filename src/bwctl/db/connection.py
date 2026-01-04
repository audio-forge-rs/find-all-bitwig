"""Database connection management."""

from contextlib import contextmanager
from typing import Generator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from bwctl.config import settings

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            settings.database.dsn,
            min_size=1,
            max_size=10,
            kwargs={"row_factory": dict_row},
        )
    return _pool


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Get a database connection from the pool."""
    pool = get_pool()
    with pool.connection() as conn:
        yield conn
