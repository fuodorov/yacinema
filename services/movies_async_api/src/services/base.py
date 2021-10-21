import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import DefaultDict, List, Optional, Type, Union

import backoff
import orjson
from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from elasticsearch import exceptions as elastic_exceptions

from core import config
from models.film import Film
from models.genre import Genre
from models.person import Person
from queryes.base import FilterInfo, PageInfo, ServiceQueryInfo, SortInfo

module_logger = logging.getLogger('Service')


class BaseService(ABC):

    @property
    @abstractmethod
    def response_model(self) -> Type[Union[Film, Genre, Person]]:
        pass

    @property
    @abstractmethod
    def elastic_index(self) -> str:
        pass

    @property
    @abstractmethod
    def elastic_search_fields(self) -> Optional[dict]:
        pass

    @property
    @abstractmethod
    def elastic_sort_fields(self) -> Optional[dict]:
        pass

    @property
    @abstractmethod
    def elastic_filter_fields(self) -> Optional[list]:
        pass

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    def _prefixed_key(self, key, prefix=None):
        if not prefix:
            prefix = self.__class__.__name__ if not prefix else None
        return '{prefix}:{key}'.format(prefix=prefix, key=key)

    def _complete_prefixed_key(self, key, prefix=None):
        """Adds a prefix containing an info about service and a kind of data to a key.

        E.g. a key 1-30:039ab... can be transformed to FilmService:List:1-30:039ab...
        """
        complete_key = key
        if prefix:
            complete_key = self._prefixed_key(complete_key, prefix)  # e.g. List:1-30:039ab...
        complete_key = self._prefixed_key(complete_key)  # e.g.  FilmService:List:1-30:039ab...
        return complete_key

    @backoff.on_exception(backoff.expo,
                          (elastic_exceptions.ConnectionError,),
                          max_time=config.TIME_LIMIT)
    async def get_by_id(self, item_id: str) -> Optional[Union[Film, Genre, Person]]:
        key_prefix = 'Details'
        item = await self._item_from_cache(item_id, key_prefix)
        if not item:
            item = await self._get_item_from_elastic(item_id)
            if not item:
                return None
            await self._put_item_to_cache(item, item.id, key_prefix)

        return item

    @backoff.on_exception(backoff.expo,
                          (elastic_exceptions.ConnectionError,),
                          max_time=config.TIME_LIMIT)
    async def get_by_query(self, query_info: ServiceQueryInfo) -> Optional[List[Union[Film, Genre, Person]]]:
        key_prefix = 'Search' if query_info.query else 'List'
        items = await self._item_from_cache(query_info.as_key(), key_prefix)
        if not items:
            items = await self._query_item_from_elastic(query_info)
            if not items:
                return None
            await self._put_item_to_cache(items, query_info.as_key(), key_prefix)

        return items

    def _elastic_pagination_request(self, page_info: PageInfo) -> DefaultDict[str, DefaultDict[str, dict]]:
        body = defaultdict(lambda: defaultdict(dict))
        body['from'] = page_info.number * page_info.size
        body['size'] = page_info.size
        body['query']['bool']['should'] = [{'match_all': {}}]
        body['query']['bool']['minimum_should_match'] = 1
        return body

    def _elastic_request_add_query(self, query: str, body: DefaultDict[str, DefaultDict[str, dict]]):
        if not query:
            return
        body['query']['bool']['should'] = []
        for field, weight in self.elastic_search_fields.items():
            match = defaultdict(lambda: defaultdict(dict))
            match['match'][field]['query'] = query
            match['match'][field]['fuzziness'] = 'auto'
            match['match'][field]['boost'] = weight
            body['query']['bool']['should'].append(match)

    def _elastic_request_add_filter(self, filter_request: FilterInfo, body: DefaultDict[str, DefaultDict[str, dict]]):
        if not filter_request:
            return
        body['query']['bool']['filter'] = []
        for field in self.elastic_filter_fields:
            uuid = filter_request.dict().get(field)
            if uuid is None:
                continue
            filter_info = defaultdict(lambda: defaultdict(dict))
            filter_info['nested']['path'] = field
            filter_info['nested']['query']['match'] = {f'{field}.id': str(uuid)}
            body['query']['bool']['filter'].append(filter_info)

    def _elastic_request_add_sort(self, sort_request: SortInfo, body: DefaultDict[str, DefaultDict[str, dict]]):
        if not sort_request:
            return
        body['sort'] = []
        sort = defaultdict(dict)
        elastic_sort_field = self.elastic_sort_fields.get(sort_request.field)
        sort[elastic_sort_field]['order'] = 'desc' if sort_request.desc else 'asc'
        body['sort'].append(sort)

    def _elastic_request_for_query(self, query_info: ServiceQueryInfo) -> dict:
        body = self._elastic_pagination_request(query_info.page)
        if query_info.query:
            self._elastic_request_add_query(query_info.query, body)
        if query_info.filter:
            self._elastic_request_add_filter(query_info.filter, body)
        if query_info.sort:
            self._elastic_request_add_sort(query_info.sort, body)

        return body

    async def _query_item_from_elastic(self, query_info: ServiceQueryInfo) -> List[Union[Film, Genre, Person]]:
        body = self._elastic_request_for_query(query_info)
        doc = await self.elastic.search(index=self.elastic_index, body=body)
        module_logger.info('Searching in %s', self.elastic_index)
        return [self.response_model(**hit['_source']) for hit in doc['hits']['hits']]

    async def _get_item_from_elastic(self, item_id: str) -> Optional[Union[Film, Genre, Person]]:
        try:
            doc = await self.elastic.get(index=self.elastic_index, id=item_id)
            module_logger.info('Getint item %s in %s', item_id, self.elastic_index)
            return self.response_model(**doc['_source'])
        except elastic_exceptions.NotFoundError:
            module_logger.info('Item %s not found in %s', item_id, self.elastic_index)
            return None

    async def _item_from_cache(self, key: str, prefix: str = None) -> Optional[Union[Union[Film, Genre, Person],
                                                                                     List[Union[Film, Genre, Person]]]]:
        cache_key = self._complete_prefixed_key(key, prefix)
        module_logger.info('Looking for item in cache (key %s)', cache_key)
        data = await self.redis.get(cache_key)
        if not data:
            return None

        module_logger.info('Cache hit (key %s)', cache_key)
        data_obj = orjson.loads(data)
        if isinstance(data_obj, list):
            return [self.response_model.parse_obj(obj) for obj in data_obj]
        return self.response_model.parse_obj(data_obj)

    async def _put_item_to_cache(self, item: Union[Union[Film, Genre, Person], List[Union[Film, Genre, Person]]],
                                 key: str, prefix: str = None):
        cache_key = self._complete_prefixed_key(key, prefix)
        module_logger.info('Putting item to cache for key %s)', cache_key)
        if isinstance(item, list):
            item_json_obj = [sub_item.dict() for sub_item in item]
        else:
            item_json_obj = item.dict()
        item_json = orjson.dumps(item_json_obj)
        await self.redis.set(cache_key, item_json, expire=config.CACHE_EXPIRATION)
