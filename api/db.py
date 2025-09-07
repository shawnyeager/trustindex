import os
from typing import Optional

try:
    import psycopg2
    from psycopg2.pool import SimpleConnectionPool
except Exception:  # pragma: no cover
    psycopg2 = None
    SimpleConnectionPool = None  # type: ignore


pool: Optional[SimpleConnectionPool] = None


def get_db_url() -> Optional[str]:
    return os.environ.get("POSTGRES_URL")


def init_pool(minconn: int = 1, maxconn: int = 5) -> None:
    global pool
    if psycopg2 is None:
        return
    url = get_db_url()
    if not url:
        return
    pool = SimpleConnectionPool(minconn, maxconn, dsn=url)


def close_pool() -> None:
    global pool
    if pool is not None:
        pool.closeall()
        pool = None


def acquire_conn():
    if pool is None:
        return None
    return pool.getconn()


def release_conn(conn) -> None:
    if pool is None or conn is None:
        return
    pool.putconn(conn)

