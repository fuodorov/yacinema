import os

from dataclasses import asdict
from datetime import datetime
from typing import Coroutine, Iterable, Optional
from psycopg2.extensions import connection as _connection

from .elastic import ElasticsearchManager
from .models import Movie, Person
from .decorators import coroutine
from .state import BaseStorage, State

LIMIT = int(os.environ.get('BATCH_LIMIT', 100))


def dispatcher(row: Iterable, name: str) -> Optional[dict]:
    _dict = {
        'genres': (lambda row: [genre.lower() for genre in row]),
        'persons_names': (lambda row: [item[1].lower() for item in row]),
        'persons': (lambda row: [Person(id=item[0], full_name=item[1].lower()) for item in row]),
    }
    return _dict[name](row) if row else None


def producer_generator(target: Coroutine, *, table_name: str, pg_conn: _connection, storage: BaseStorage):
    cursor = pg_conn.cursor()
    cursor.arraysize = LIMIT

    state_manager = State(storage=storage)
    default_date = str(datetime(year=1700, month=1, day=1))
    current_state = state_manager.state.get(table_name, default_date)

    cursor.execute(f"""SELECT id, modified FROM content.{table_name} WHERE modified >= %s ORDER BY modified""",
                   (current_state,))

    while True:
        batch_result = cursor.fetchmany()
        ids_list = [item['id'] for item in batch_result]

        if not ids_list:
            break

        target.send(ids_list)
        state_manager.set_state(key=table_name, value=str(batch_result[-1]['modified']))


@coroutine
def enricher_coroutine(target: Coroutine, *, m2m_table_name: str, column_name: str, pg_conn: _connection):
    cursor = pg_conn.cursor()
    cursor.arraysize = LIMIT

    while ids_list := (yield):
        cursor.execute(f"""SELECT DISTINCT film_work_id FROM content.{m2m_table_name} WHERE {column_name} IN %s""",
                       (tuple(ids_list),))

        while True:
            batch_result = cursor.fetchmany()
            ids_list = [item['film_work_id'] for item in batch_result]

            if not ids_list:
                break

            target.send(ids_list)


@coroutine
def merger_coroutine(target: Coroutine, *, pg_conn: _connection) -> None:
    cursor = pg_conn.cursor()

    while ids_list := (yield):
        cursor.execute("""
        SELECT content.film_work.id, content.film_work.title, content.film_work.description, content.film_work.rating,
            array_agg(DISTINCT content.genre.name) as genres,
            array_agg(DISTINCT ARRAY["content"."person"."id"::text, "content"."person"."full_name"]) FILTER (WHERE "content"."person_film_work"."role" = 'actor') AS "actors",
            array_agg(DISTINCT ARRAY["content"."person"."id"::text, "content"."person"."full_name"]) FILTER (WHERE "content"."person_film_work"."role" = 'writer') AS "writers",
            array_agg(DISTINCT ARRAY["content"."person"."id"::text, "content"."person"."full_name"]) FILTER (WHERE "content"."person_film_work"."role" = 'director') AS "directors"
        FROM content.film_work
        LEFT JOIN content.genre_film_work ON content.genre_film_work.film_work_id = content.film_work.id
        LEFT JOIN content.genre ON content.genre.id = content.genre_film_work.genre_id
        LEFT JOIN content.person_film_work ON content.person_film_work.film_work_id = content.film_work.id
        LEFT JOIN content.person ON content.person.id = content.person_film_work.person_id
        WHERE content.film_work.id IN %s
        GROUP BY content.film_work.id
        """, (tuple(ids_list),))

        raw_rows = cursor.fetchall()
        target.send(raw_rows)


@coroutine
def transform_coroutine(target):
    while raw_rows := (yield):
        movies = []
        for row in raw_rows:
            movies.append(Movie(
                id=row['id'],
                title=row['title'],
                description=row['description'],
                rating=(float(row['rating']) if row['rating'] else None),
                genres=dispatcher(row['genres'], 'genres'),
                actors_names=dispatcher(row['actors'], 'persons_names'),
                writers_names=dispatcher(row['actors'], 'persons_names'),
                directors_names=dispatcher(row['actors'], 'persons_names'),
                actors=dispatcher(row['actors'], 'persons'),
                writers=dispatcher(row['writers'], 'persons'),
                directors=dispatcher(row['directors'], 'persons')
            ))

        target.send(movies)


@coroutine
def loader_coroutine(es_manager: ElasticsearchManager, index_name: str):
    while movies_list := (yield):
        movies_list = (asdict(movie) for movie in movies_list)
        es_manager.load(records=movies_list, index_name=index_name)
