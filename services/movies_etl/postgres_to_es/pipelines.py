import abc
import datetime as dt
import logging
from time import sleep
from typing import Generator, List

from config import ETL_DEFAULT_DATE, ETL_SYNC_DELAY
from elastic import ElasticsearchLoader
from models import Film, Genre, Person, ShortFilm, ShortGenre, ShortPerson
from postgres import PostgresProducer
from queries import (FW_QUERY, GENRE_FW_QUERY, GENRE_QUERY, LAST_FW_QUERY,
                     LAST_GENRE_QUERY, LAST_PERSON_QUERY, PERSON_FW_QUERY,
                     PERSON_QUERY)
from state import State
from utils import coroutine


class BasePipeline:
    index: str = ''

    def __init__(self, state: State, db_adapter: PostgresProducer, es_loader: ElasticsearchLoader):
        self.state = state
        self.db_adapter = db_adapter
        self.es_loader = es_loader
        self.logger = logging.getLogger(self.__class__.__name__)
        self.state_key = f'{self.index}_last_updated'

        self.db_adapter.init()
        self.es_loader.init(self.index)

    @abc.abstractmethod
    def etl_process(self) -> None:
        pass

    @abc.abstractmethod
    def transform(self, target: Generator) -> None:
        pass

    @coroutine
    def enrich(self, query: str, target: Generator) -> Generator:
        while True:
            context = []
            ids = (yield)
            self.logger.info('Got %d ids', len(ids))
            if ids:
                for chunck_rows in self.db_adapter.execute(query, list(ids)):
                    context.extend(chunck_rows)

                target.send(context)

    @coroutine
    def collect_updated_ids(self, query: str, target: Generator) -> Generator:
        while True:
            result = []
            query_args = (yield)
            if query_args:
                for chunck_rows in self.db_adapter.execute(query, query_args):
                    result.extend([row['id'] for row in chunck_rows])

            target.send(result)

    @coroutine
    def es_loader_coro(self, index_name: str) -> Generator:
        while rows := (yield):
            self.es_loader.load_to_es(rows, index_name)

    def event_loop(self, generators: List[Generator]):
        while True:
            state_value = self.state.get_state(self.state_key) or ETL_DEFAULT_DATE
            self.logger.info('Start ETL process for %s: %s', self.state_key, state_value)
            for generator in generators:
                generator.send(state_value)
            self.state.set_state(self.state_key, str(dt.datetime.now()))
            self.logger.info('ETL process is finished.  Sleep: %d seconds', ETL_SYNC_DELAY)
            sleep(ETL_SYNC_DELAY)


class FilmWorkPipeline(BasePipeline):
    index = 'movies'

    @coroutine
    def enrich(self, query: str, target: Generator) -> Generator:
        while True:
            context = []
            ids = set()
            fw_ids_from_person = (yield)
            ids.update(fw_ids_from_person)
            self.logger.info('Got %d film_work ids from person etl', len(fw_ids_from_person))

            fw_ids_from_genre = (yield)
            ids.update(fw_ids_from_genre)
            self.logger.info('Got %d film_work ids from genre etl', len(fw_ids_from_genre))

            fw_ids_from_fw = (yield)
            ids.update(fw_ids_from_fw)
            self.logger.info('Got %d film_work ids from film_work etl', len(fw_ids_from_fw))

            self.logger.info('Total unique film_work ids to update: %d', len(ids))
            if ids:
                for chunck_rows in self.db_adapter.execute(query, list(ids)):
                    context.extend(chunck_rows)

                target.send(context)

    @coroutine
    def transform(self, target: Generator) -> Generator:
        while rows := (yield):
            movies = {}
            for row in rows:
                if row['fw_id'] not in movies:
                    movies[row['fw_id']] = Film(
                        id=row['fw_id'],
                        title=row['title'],
                        rating=row['rating'],
                        description=row['description'],
                        type=row['type'],
                        creation_date=row['creation_date'],
                    )
                movies[row['fw_id']].add_genre(
                    ShortGenre(
                        id=row['genre_id'],
                        name=row['genre_name'])
                )
                movies[row['fw_id']].add_person(
                    ShortPerson(
                        id=row['person_id'],
                        name=row['person_name']),
                    role=row['person_role']
                )
            target.send([movie.as_dict for movie in movies.values()])

    def etl_process(self):
        es_target = self.es_loader_coro(self.index)
        transform_target = self.transform(es_target)
        enrich_target = self.enrich(FW_QUERY, transform_target)

        person_fw_target = self.collect_updated_ids(PERSON_FW_QUERY, enrich_target)
        genre_fw_target = self.collect_updated_ids(GENRE_FW_QUERY, enrich_target)

        updated_fw_target = self.collect_updated_ids(LAST_FW_QUERY, enrich_target)
        updated_person_target = self.collect_updated_ids(LAST_PERSON_QUERY, person_fw_target)
        updated_genre_target = self.collect_updated_ids(LAST_GENRE_QUERY, genre_fw_target)

        self.event_loop([updated_person_target, updated_genre_target, updated_fw_target])


class GenrePipeline(BasePipeline):
    index = 'genres'

    @coroutine
    def transform(self, target: Generator) -> Generator:
        while rows := (yield):
            genre = {}
            for row in rows:
                if row['genre_id'] not in genre:
                    genre[row['genre_id']] = Genre(
                        id=row['genre_id'],
                        name=row['genre_name'],
                        description=row['genre_description']
                    )
            target.send([genre.as_dict for genre in genre.values()])

    def etl_process(self):
        es_target = self.es_loader_coro(self.index)
        transform_target = self.transform(es_target)
        enrich_target = self.enrich(GENRE_QUERY, transform_target)

        updated_genre_target = self.collect_updated_ids(LAST_GENRE_QUERY, enrich_target)

        self.event_loop([updated_genre_target])


class PersonPipeline(BasePipeline):
    index = 'persons'

    @coroutine
    def transform(self, target: Generator) -> Generator:
        while rows := (yield):
            people = {}
            for row in rows:
                if row['person_id'] not in people:
                    people[row['person_id']] = Person(
                        id=row['person_id'],
                        name=row['person_name']
                    )
                people[row['person_id']].add_role(
                    role=row['person_role']
                )
                people[row['person_id']].add_film(
                    ShortFilm(
                        id=row['fw_id'],
                        title=row['fw_title'],
                        type=row['fw_type'],
                        rating=row['fw_rating'],
                    )
                )
            target.send([person.as_dict for person in people.values()])

    def etl_process(self):
        es_target = self.es_loader_coro(self.index)
        transform_target = self.transform(es_target)
        enrich_target = self.enrich(PERSON_QUERY, transform_target)

        updated_person_target = self.collect_updated_ids(LAST_PERSON_QUERY, enrich_target)

        self.event_loop([updated_person_target])
