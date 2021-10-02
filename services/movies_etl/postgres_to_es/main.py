import logging
import os

from elastic import ElasticsearchLoader
from postgres import PostgresProducer
from models import ModeETL
from state import JsonFileStorage, State
from pipelines import FilmWorkPipeline, PersonPipeline, GenrePipeline

ETL_MODE = os.environ.get('ETL_MODE')

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('root')

# Вдохновленный вебинаром...
if __name__ == '__main__':
    logger.info(f'Start ETL application with {ETL_MODE} mode')

    state = State(
        JsonFileStorage(os.environ.get('ETL_FILE_STATE'))
    )
    es_loader = ElasticsearchLoader(
        [f"http://{os.environ.get('ELASTICSEARCH_HOST')}:{os.environ.get('ELASTICSEARCH_PORT')}"]
    )
    db_adapter = PostgresProducer({
        'dbname': os.environ.get('POSTGRES_NAME'),
        'user': os.environ.get('POSTGRES_USER'),
        'password': os.environ.get('POSTGRES_PASSWORD'),
        'host': os.environ.get('POSTGRES_HOST'),
        'port': os.environ.get('POSTGRES_PORT'),
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
