import os

from psycopg2.extras import DictCursor
import psycopg2

from utils.etl import ETL

if __name__ == '__main__':
    dsl = {
        'dbname': os.environ['POSTGRES_DB'],
        'user': os.environ['POSTGRES_USER'],
        'password': os.environ['POSTGRES_PASSWORD'],
        'host': os.environ['POSTGRES_HOST'],
        'port': os.environ['POSTGRES_PORT']
    }
    es_host = os.environ['ELASTICSEARCH_HOST']
    es_port = os.environ['ELASTICSEARCH_PORT']
    with psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn:
        mergePipe = ETL(file_path='state.json', pg_conn=pg_conn, es_url=f"http://{es_host}:{es_port}/", dsl=dsl)
        mergePipe.initial_update()
        mergePipe.start_merge()
