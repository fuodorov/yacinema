import logging
import os

from config import (ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, ETL_FILE_STATE,
                    ETL_MODE, POSTGRES_HOST, POSTGRES_NAME, POSTGRES_PASSWORD,
                    POSTGRES_PORT, POSTGRES_USER)
from elastic import ElasticsearchLoader
from models import ModeETL
from pipelines import FilmWorkPipeline, GenrePipeline, PersonPipeline
from postgres import PostgresProducer
from state import JsonFileStorage, State

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('root')


def main():
    logger.info('Start ETL application with %s mode', ETL_MODE)

    state = State(
        JsonFileStorage(ETL_FILE_STATE)
    )
    es_loader = ElasticsearchLoader(
        ['http://{host}:{port}'.format(host=ELASTICSEARCH_HOST, port=ELASTICSEARCH_PORT)]
    )
    db_adapter = PostgresProducer({
        'dbname': POSTGRES_NAME,
        'user': POSTGRES_USER,
        'password': POSTGRES_PASSWORD,
        'host': POSTGRES_HOST,
        'port': POSTGRES_PORT,
    })

    if ETL_MODE == ModeETL.FILM_WORK.value:
        film_work = FilmWorkPipeline(state, db_adapter, es_loader)
        film_work.etl_process()
    elif ETL_MODE == ModeETL.PERSON.value:
        person = PersonPipeline(state, db_adapter, es_loader)
        person.etl_process()
    elif ETL_MODE == ModeETL.GENRE.value:
        genre = GenrePipeline(state, db_adapter, es_loader)
        genre.etl_process()
    else:
        logger.warning('Mode ETL must be from a list: %s', ', '.join([mode.value for mode in ModeETL]))
        logger.info('End ETL application with %s mode', ETL_MODE)


if __name__ == '__main__':
    main()
