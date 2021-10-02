import json
import logging

from pathlib import Path
from typing import Generator, List
from elasticsearch import Elasticsearch, exceptions

from utils import backoff

module_logger = logging.getLogger('ElasticsearchLoader')


class ElasticsearchLoader:
    def __init__(self, hosts: list, chunk_size: int = 500):
        self.client = Elasticsearch(hosts=hosts)
        self.chunk_size = chunk_size
        self.init_indexes()

    def init_indexes(self):
        index_dir = Path(__file__).resolve(strict=True).parent.joinpath('indexes')
        files = index_dir.glob('**/*.json')
        for file in files:
            index = file.stem
            with open(file, 'r') as index_file:
                data = json.load(index_file)
            try:
                self.client.indices.create(index=index, body=data)
            except exceptions.ElasticsearchException:
                module_logger.warning(f'Index already exist: {index}')

    def load_to_es(self, records: List[dict], index_name: str) -> None:
        for prepared_query in self._get_chunk_query(records, index_name):
            str_query = '\n'.join(prepared_query) + '\n'
            self._post_to_es(str_query, index_name)
            module_logger.info(f'Post {len(prepared_query)} items to elastic search')

    @backoff(Exception, logger=module_logger)
    def _post_to_es(self, query: str, index: str) -> None:
        self.client.bulk(body=query, index=index)
        self.client.indices.refresh(index=index)

    def _get_chunk_query(self, rows: List[dict], index_name: str) -> Generator[List[str], None, None]:
        prepared_query = []
        chunked_rows = [rows[i:i+self.chunk_size] for i in range(0, len(rows), self.chunk_size)]

        for chunk in chunked_rows:
            for row in chunk:
                prepared_query.extend([
                    json.dumps({'index': {'_index': index_name, '_id': row['id']}}),
                    json.dumps(row)
                ])
            yield prepared_query
            prepared_query.clear()
