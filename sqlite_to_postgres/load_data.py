import os
import sqlite3
import psycopg2

from pathlib import Path
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

from utils.loader import SQLiteLoader
from utils.saver import PostgresSaver


def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    """Basic method for loading data from SQLite into Postgres."""
    postgres_saver = PostgresSaver(pg_conn)
    sqlite_loader = SQLiteLoader(connection)

    postgres_saver.save_all_data(sqlite_loader.load_movies())


if __name__ == '__main__':
    dsl = {
        'dbname': os.getenv('DB_NAME', 'movies'),
        'user': os.getenv('DB_USER', 'postgres'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
    }
    sqlite_path = Path(__file__).parent.joinpath('db.sqlite')

    with sqlite3.connect(sqlite_path) as sqlite_conn, psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn:
        load_from_sqlite(sqlite_conn, pg_conn)
