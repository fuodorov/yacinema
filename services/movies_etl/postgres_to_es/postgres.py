import psycopg2

from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

from .decorators import backoff


@backoff()
def get_pg_conn(dsn: dict) -> _connection:
    return psycopg2.connect(**dsn, cursor_factory=DictCursor)
