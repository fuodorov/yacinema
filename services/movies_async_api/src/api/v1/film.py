import logging
from http import HTTPStatus
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from models.film import BaseFilm, Film
from queryes.base import QueryParamsBase, ServiceQueryInfo
from queryes.film import FilmQueryParamsInfo, FilmQueryParamsSearch
from services.film import FilmService, get_film_service
from api.auth.required import AuthRequired, AuthInfo

router = APIRouter()

module_logger = logging.getLogger('FilmAPI')


async def get_films(params: QueryParamsBase, film_service: FilmService, pro_user: bool) -> List[BaseFilm]:
    module_logger.info('Getting films with query (%s)', params)
    service_query_info = ServiceQueryInfo.parse_obj(params.asdict())
    if not pro_user:
        service_query_info.max_rating = 7.0
    films = await film_service.get_by_query(service_query_info)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return [Film(**film.dict()) for film in films]


@router.get('/',
            response_model=List[BaseFilm],
            description='Info about films with pagination, filtering by genre and sorting by rating and title',
            response_description='Films list with base info')
async def films_info(params: FilmQueryParamsInfo = Depends(),
                     auth_info: AuthInfo = Depends(AuthRequired('pro_read')),
                     film_service: FilmService = Depends(get_film_service)) -> List[BaseFilm]:
    pro_user = bool(auth_info and auth_info.permissions_valid)
    films = await get_films(params, film_service, pro_user)
    return films


@router.get('/search',
            response_model=List[BaseFilm],
            description='''Films full-text search with pagination, filtering by genre and sorting by rating, title, 
                        and relevance''',
            response_description='Films list with base info')
async def films_search(params: FilmQueryParamsSearch = Depends(),
                       auth_info: AuthInfo = Depends(AuthRequired('pro_read')),
                       film_service: FilmService = Depends(get_film_service)) -> List[BaseFilm]:
    pro_user = bool(auth_info and auth_info.permissions_valid)
    films = await get_films(params, film_service, pro_user)
    return films


@router.get('/{film_id}',
            response_model=Film,
            description='Detailed info about film including description, rating, genres, persons etc',
            response_description='Film details')
async def film_details(film_id: UUID,
                       auth_info: AuthInfo = Depends(AuthRequired('pro_read')),
                       film_service: FilmService = Depends(get_film_service)) -> Film:
    module_logger.info('Getting film with id (%s)', film_id)
    film = await film_service.get_by_id(str(film_id))
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    pro_user = bool(auth_info and auth_info.permissions_valid)
    if not pro_user and film.rating > 7.0:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail='Not enough permissions')

    return Film(**film.dict())
