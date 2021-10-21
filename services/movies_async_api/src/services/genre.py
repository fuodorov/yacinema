from functools import lru_cache

from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.genre import Genre
from services.base import BaseService


class GenreService(BaseService):
    response_model = Genre
    elastic_index = 'genres'
    elastic_search_fields = {'name': 1.5, 'description': 1.0}
    elastic_sort_fields = {'name': 'name.raw'}
    elastic_filter_fields = []


@lru_cache()
def get_genre_service(redis: Redis = Depends(get_redis),
                      elastic: AsyncElasticsearch = Depends(get_elastic)) -> GenreService:
    return GenreService(redis, elastic)
