from functools import lru_cache

from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.person import Person
from services.base import BaseService


class PersonService(BaseService):
    response_model = Person
    elastic_index = 'persons'
    elastic_search_fields = {'name': 1.5}
    elastic_sort_fields = {'full_name': 'name.raw'}
    elastic_filter_fields = ['films']


@lru_cache()
def get_person_service(redis: Redis = Depends(get_redis),
                       elastic: AsyncElasticsearch = Depends(get_elastic)) -> PersonService:
    return PersonService(redis, elastic)
