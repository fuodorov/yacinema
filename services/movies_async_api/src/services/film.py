from functools import lru_cache

from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film
from services.base import BaseService


class FilmService(BaseService):
    response_model = Film
    elastic_index = 'movies'
    elastic_search_fields = {'title': 1.5, 'description': 1.0}
    elastic_sort_fields = {'imdb_rating': 'rating', 'title': 'title.raw'}
    elastic_filter_fields = ['genre', 'person']


@lru_cache()
def get_film_service(redis: Redis = Depends(get_redis),
                     elastic: AsyncElasticsearch = Depends(get_elastic)) -> FilmService:
    return FilmService(redis, elastic)
