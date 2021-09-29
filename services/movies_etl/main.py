import os

from postgres_to_es.elastic import ElasticsearchManager
from postgres_to_es.postgres import get_pg_conn
from postgres_to_es.etl import ETLManager, ProducerTable
from postgres_to_es.state import JsonFileStorage

dsl = {
    'dbname': os.environ.get('POSTGRES_DB'),
    'user': os.environ.get('POSTGRES_USER'),
    'password': os.environ.get('POSTGRES_PASSWORD'),
    'host': os.environ.get('POSTGRES_HOST'),
    'port': os.environ.get('POSTGRES_PORT')
}


if __name__ == '__main__':
    pg_conn = get_pg_conn(dsl)
    es_manager = ElasticsearchManager(f"http://{os.environ.get('ELASTICSEARCH_HOST')}:{os.environ.get('ELASTICSEARCH_PORT')}/")

    for const in ProducerTable:
        ETLManager(
            producer_table=const.value,
            pg_conn=pg_conn,
            es_manager=es_manager,
            storage=JsonFileStorage(f'{const.value}_state.json'),
            index_name=os.environ.get('INDEX', 'movies')
        ).start()
