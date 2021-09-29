import json
import requests

from typing import List, TextIO
from urllib.parse import urljoin

from .decorators import backoff


class ElasticsearchManager:
    def __init__(self, url: str):
        self.url = url

    def _get_bulk_query(self, rows: List[dict], index_name: str) -> List[str]:
        prepared_query = []
        for row in rows:
            prepared_query.extend([
                json.dumps({'index': {'_index': index_name, '_id': row['id']}}),
                json.dumps(row)
            ])
        return prepared_query

    @backoff()
    def is_index_exist(self, index_name: str) -> bool:
        return True if requests.head(urljoin(self.url, index_name)).status_code == 200 else False

    @backoff()
    def create_index(self, fp: TextIO, index_name: str) -> None:
        if not self.is_index_exist(index_name):
            requests.put(urljoin(self.url, index_name), json=json.load(fp))

    @backoff()
    def delete_index(self, index_name: str):
        requests.delete(urljoin(self.url, index_name))

    @backoff()
    def load(self, records: List[dict], index_name: str) -> None:
        response = requests.post(
            urljoin(self.url, '_bulk'),
            data='\n'.join(self._get_bulk_query(records, index_name)) + '\n',
            headers={'Content-Type': 'application/x-ndjson'}
        )
        json.loads(response.content.decode())
