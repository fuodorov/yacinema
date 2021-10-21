import logging
from http import HTTPStatus
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from models.film import BaseFilm, Film
from queryes.base import QueryParamsBase, ServiceQueryInfo
from queryes.film import FilmQueryParamsInfo, FilmQueryParamsSearch
from services.film import FilmService, get_film_service

router = APIRouter()

module_logger = logging.getLogger('FilmAPI')


async def get_films(params: QueryParamsBase, film_service: FilmService) -> List[BaseFilm]:
    module_logger.info('Getting films with query (%s)', params)
    service_query_info = ServiceQueryInfo.parse_obj(params.asdict())
    films = await film_service.get_by_query(service_query_info)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return [Film(**film.dict()) for film in films]


@router.get('/', response_model=List[BaseFilm])
async def films_info(params: FilmQueryParamsInfo = Depends(),
                     film_service: FilmService = Depends(get_film_service)) -> List[BaseFilm]:
    films = await get_films(params, film_service)
    return films


@router.get('/search', response_model=List[BaseFilm])
async def films_search(params: FilmQueryParamsSearch = Depends(),
                       film_service: FilmService = Depends(get_film_service)) -> List[BaseFilm]:
    films = await get_films(params, film_service)
    return films


@router.get('/{film_id}', response_model=Film)
async def film_details(film_id: UUID, film_service: FilmService = Depends(get_film_service)) -> Film:
    module_logger.info('Getting film with id (%s)', film_id)
    film = await film_service.get_by_id(str(film_id))
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return Film(**film.dict())
