import os
from datetime import datetime, timezone, timedelta
import json
import time
import logging
from typing import Callable

from elasticsearch import Elasticsearch, exceptions, helpers
import psycopg2
import backoff
from psycopg2.extras import DictCursor

from .state import JsonFileStorage, State
from models.film_work import FilmWork
from models.genre import Genre
from models.person import Person
from .coroutine import coroutine
from .queries import movies_query, genres_query, persons_query

logging.basicConfig(level=logging.WARNING)
logging.getLogger('backoff').addHandler(logging.StreamHandler())


class ETL:
    """ETL manager."""
    # ToDo:
    #  - с точки зрения ETL - желательно все-таки разбить этот класс на 3,
    #  соответствующие каждому этапу и сделать их минимально связными.
    #  Чтобы каждый компонент просто работал с полученной порцией данных.
    #  Меньшая связность компонентов - залог их простого расширения
    #  - Я долго думал, разбивать или нет... Решил, что не нужно
    #  ETL = PostgresProducer + ElasticsearchLoader + Pipeline
    #  Чуть не успеваю до дедлайна, выкладываю то, что есть :-/

    batch_limit = int(os.environ.get('BATCH_LIMIT', 100))
    update_interval = int(os.environ.get('UPDATE_INTERVAL', 1))
    main_tables = ('content.person', 'content.genre', 'content.film_work')
    associated_tables = ('content.genre_film_work', 'content.person_film_work')

    def __init__(self, file_path: str, pg_conn: psycopg2.connect, es_url: str, dsl: dict):
        self.conn = pg_conn
        self.cursor = self.conn.cursor()
        self.es = Elasticsearch(es_url)
        self.dsl = dsl
        self.postgresState = State(JsonFileStorage(file_path))

    @backoff.on_exception(backoff.expo, (exceptions.ConnectionError, exceptions.ConnectionTimeout))
    def clear_index_data(self, index_name: str):
        """Clears all data within the index."""
        self.es.indices.delete(index=index_name, ignore=404)
        self.es.indices.create(index=index_name)

    def initial_update(self):
        """Puts all entries from Postgres into Elasticsearch and sets the update time."""
        # ToDo:
        #  - это не очень хороший подход) зачем нам удалять индекс, если только для дебага..
        #  но тут у нас продакш код. можем проверять есть ли индекс и создавать, если нет.
        #  - У нас же при запуске кинотеатра индексы в Postgres генерируются заново,
        #  и использовать существующие записи в es не удастся?
        logging.warning('Wait while all data will be loaded to ES...')
        self.clear_index_data('movies')
        self.clear_index_data('genres')
        self.clear_index_data('persons')
        updater = self.update_es()
        transform = self.transform_received(updater)
        self.initial_load_from_psql(transform)
        updater.close()
        transform.close()
        current_time = (datetime.now(timezone.utc)).strftime("%m-%d-%Y %H:%M:%S")
        for table_name in self.main_tables:
            self.postgresState.set_state(table_name, current_time)
        logging.warning('Now ES is up-to-date with postgres')

    def initial_load_from_psql(self, target: Callable):
        """Loads all entries from Postgres in packs and sends to the handler."""
        @backoff.on_exception(backoff.expo, psycopg2.Error)
        def load(self, target):
            queries = [{'index': 'genres', 'query': genres_query},
                       {'index': 'movies', 'query': movies_query},
                       {'index': 'persons', 'query': persons_query}]
            for query in queries:
                offset = 0
                while True:
                    q = query['query'](offset)
                    self.cursor.execute(q)
                    offset += self.batch_limit
                    all_rows = [dict(row) for row in self.cursor]
                    target.send({'index': query['index'], 'data': all_rows})
                    if len(all_rows) < self.batch_limit:
                        break
        load(self, target)

    @backoff.on_exception(backoff.expo, (exceptions.ConnectionError, exceptions.ConnectionTimeout))
    def update_es_instances(self, index: str, data: list):
        """Updates a bunch of entries in the index in Elasticsearch."""
        logging.warning(f"""Updating {index} in ES""")
        doc_data = [{
            '_op_type': 'update',
            '_type': '_doc',
            '_index': index,
            '_id': instance.id,
            'doc': instance.dict(),
            'doc_as_upsert': True
        } for instance in data]
        helpers.bulk(self.es, doc_data)

    @coroutine
    def update_es(self):
        """Updates entries in the Elasticsearch or adds if there are none."""
        while True:
            instances_to_update = (yield)
            self.update_es_instances(instances_to_update['index'], instances_to_update['data'])

    def movies_transform_received(self):
        pass

    @coroutine
    def transform_received(self, target: Callable):
        """Brings Postgres entries to an Elasticsearch-appropriate structure."""
        roles_correlation = {'director': 'directors', 'actor': 'actors', 'writer': 'writers'}
        while True:
            rows = (yield)
            index = rows['index']
            rows = rows['data']
            data = []
            for row in rows:
                if index == 'movies':
                    fw_id = row['fw_id']
                    filmwork = next((item for item in data if item.id == fw_id), False)
                    if not filmwork:
                        data.append(FilmWork(id=row['fw_id'], title=row['title'], rating=row['rating'],
                                    description=row['description']))
                        filmwork = data[-1]
                    role_name = row['role']
                    if role_name:
                        role_field_name = roles_correlation[row['role']]
                        role_field_value = getattr(filmwork, role_field_name)
                        name = row['full_name']
                        if not name in role_field_value:
                            role_field_value.append(name)
                        setattr(filmwork, role_field_name, role_field_value)
                    genre = {'name': row['name'], 'id': row['g_id']}
                    if not genre in filmwork.genres:
                        filmwork.genres.append(genre)
                elif index == 'genres':
                    genre = next((item for item in data if item.id == row["g_id"]), False)
                    if not genre:
                        data.append(Genre(id=row['g_id'], name=row['name']))
                        genre = data[-1]
                    fw_id = row['fw_id']
                    if not fw_id in genre.film_works:
                        genre.film_works.append(fw_id)

                elif index == 'persons':
                    person = next((item for item in data if item.id == row["p_id"]), False)
                    if not person:
                        data.append(Person(id=row['p_id'], full_name=row['full_name']))
                        person = data[-1]
                    fw_id = row['fw_id']
                    role = row['person_role']
                    if not fw_id in person.film_ids:
                        person.film_ids.append(fw_id)
                    if not role in person.role:
                        person.role.append(role)

            target.send({'index': index, 'data': data})

    @coroutine
    def get_associated_instances(self, target: Callable):
        """Makes a JOIN of the other tables linked to the entry."""
        references = [
            {'table_name': 'content.person', 'join_table_name': 'content.person_film_work', 'field': 'person_id'},
            {'table_name': 'content.genre', 'join_table_name': 'content.genre_film_work', 'field': 'genre_id'},
            {'table_name': 'content.film_work', 'join_table_name': None, 'field': None}
        ]

        @backoff.on_exception(backoff.expo, psycopg2.Error, on_backoff=self.postgres_backoff_handler)
        def join_all_fw_tables(self, fw_ids: list, target: Callable):
            # search for all related entries from other tables
            self.cursor.execute(f"""SELECT
                                        fw.id as fw_id, 
                                        fw.title, 
                                        fw.description, 
                                        fw.rating, 
                                        fw.type, 
                                        fw.created, 
                                        fw.modified, 
                                        pfw.role, 
                                        p.id, 
                                        p.full_name,
                                        g.name,
                                        g.id as g_id
                                    FROM content.film_work fw
                                    LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
                                    LEFT JOIN content.person p ON p.id = pfw.person_id
                                    LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
                                    LEFT JOIN content.genre g ON g.id = gfw.genre_id
                                    WHERE fw.id IN {fw_ids};""")
            all_rows = [dict(row) for row in self.cursor]
            target.send({'index': 'movies', 'data': all_rows})

        @backoff.on_exception(backoff.expo, psycopg2.Error, on_backoff=self.postgres_backoff_handler)
        def join_genres_persons_tables(self, table_name: str, ids: list, target: Callable):
            if table_name == 'content.genre':
                self.cursor.execute(f"""SELECT
                                                g.name,
                                                g.id as g_id,
                                                fw.id as fw_id
                                        FROM content.genre g
                                        LEFT JOIN content.genre_film_work gfw ON gfw.genre_id = g.id
                                        LEFT JOIN content.film_work fw ON fw.id = gfw.film_work_id
                                        WHERE g.id IN {ids};""")
                all_rows = [dict(row) for row in self.cursor]
                target.send({'index': 'genres', 'data': all_rows})
            elif table_name == 'content.person':
                self.cursor.execute(f"""SELECT
                                                p.full_name,
                                                p.id as p_id,
                                                fw.id as fw_id,
                                                pfw.role as person_role
                                        FROM content.person p
                                        LEFT JOIN content.person_film_work pfw ON pfw.person_id = p.id
                                        LEFT JOIN content.film_work fw ON fw.id = pfw.film_work_id
                                        WHERE p.id IN {ids};""")
                all_rows = [dict(row) for row in self.cursor]
                target.send({'index': 'persons', 'data': all_rows})

        @backoff.on_exception(backoff.expo, psycopg2.Error, on_backoff=self.postgres_backoff_handler())
        def get_associated_movies(self, reference: dict, ids: list):
            """Search for all films related to this entry."""
            sql_query = f"""SELECT 
                                fw.id, 
                                fw.modified
                            FROM content.film_work fw
                            LEFT JOIN {reference['join_table_name']} pfw ON pfw.film_work_id = fw.id
                            WHERE pfw.{reference['field']} IN {ids}
                            ORDER BY fw.modified DESC
                            LIMIT {self.batch_limit};"""
            self.cursor.execute(sql_query)
            dict_cur = (dict(row) for row in self.cursor)
            fw_ids = tuple([item['id'] for item in dict_cur])
            if len(fw_ids) == 0:
                return None
            if len(fw_ids) == 1:
                fw_ids = f"""('{fw_ids[0]}')"""
            return fw_ids

        while True:
            table_name, ids, time = (yield)
            if len(ids) == 1:
                ids = f"""('{ids[0]}')"""
            if table_name == 'content.film_work':
                fw_ids = ids
            else:
                join_genres_persons_tables(self, table_name, ids, target)
                reference = next(item for item in references if item['table_name'] == table_name)
                fw_ids = get_associated_movies(self, reference, ids)
                if fw_ids is None:
                    continue
            join_all_fw_tables(self, fw_ids, target)

    def postgres_backoff_handler(self, *args, **kwargs):
        self.reconnect_postgres()

    def reconnect_postgres(self):
        self.conn = psycopg2.connect(
            **self.dsl, cursor_factory=DictCursor)
        self.cursor = self.conn.cursor()

    def get_last_table_updates(self, table_name: str, target: Callable):
        """Search for recent changes to this table."""
        try:
            update_time_str = self.postgresState.state[table_name]
            update_time = datetime.strptime(update_time_str if update_time_str else "01-01-1970 00:00:00",
                                            "%m-%d-%Y %H:%M:%S")
            self.cursor.execute(f"""SELECT 
                                        id, 
                                        modified
                                    FROM {table_name}
                                    WHERE modified > '{update_time}'
                                    ORDER BY modified DESC
                                    LIMIT {self.batch_limit};""")
            dict_cur = (dict(row) for row in self.cursor)
        except psycopg2.Error as e:
            logging.warning(f'{e}. Waiting for Postgres to wake up...')
            try:
                self.reconnect_postgres()
            except psycopg2.Error as e:
                pass
            return
        modified = []
        ids = []
        for item in dict_cur:
            ids.append(item['id'])
            modified.append(item['modified'])
        if len(ids) > 0:
            update_time = modified[0]
            update_time = update_time + timedelta(seconds=2)
            update_time_str = update_time.strftime("%m-%d-%Y %H:%M:%S")
            self.postgresState.set_state(table_name, update_time_str)
            ids = tuple(ids)
            info_to_send = (table_name, ids, update_time)
            target.send(info_to_send)

    def get_updated_instances(self, target: Callable):
        """Search for entries that have changed since the last status update."""
        while True:
            for table_name in self.main_tables:
                self.get_last_table_updates(table_name, target)
            time.sleep(self.update_interval)

    def start_merge(self):
        """Running an endless data update cycle from Postgres to ES."""
        updater = self.update_es()
        transform = self.transform_received(updater)
        associated_loader = self.get_associated_instances(transform)
        self.get_updated_instances(associated_loader)
