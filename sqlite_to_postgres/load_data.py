import sqlite3

import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor


def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    """Основной метод загрузки данных из SQLite в Postgres"""
    # postgres_saver = PostgresSaver(pg_conn)
    # sqlite_loader = SQLiteLoader(connection)

    # data = sqlite_loader.load_movies()
    # postgres_saver.save_all_data(data)


if __name__ == '__main__':
    dsl = {'dbname': 'movies_database', 'user': 'postgres', 'password': 1234, 'host': '127.0.0.1', 'port': 5432}
    with sqlite3.connect('db.sqlite') as sqlite_conn, psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn:
        load_from_sqlite(sqlite_conn, pg_conn)
