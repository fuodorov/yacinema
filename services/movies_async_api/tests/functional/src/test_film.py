import copy
import json
import pytest
from contextlib import asynccontextmanager
from http import HTTPStatus
from itertools import chain

from settings import ELASTIC_FILM_INDEX, ELASTIC_FILM_DATA, ELASTIC_FILM_SCHEMA
from utils.lists import drop_details, get_uuids, get_page_items, is_sorted
from utils.mappings import (films_es_to_api_mapping, persons_es_to_api_mapping, genres_es_to_api_mapping,
                            get_translated_dict)
from utils.objects import contains_text
from utils.tests import TestAPIBase


pytestmark = pytest.mark.asyncio


@pytest.fixture(scope='session')
def endpoint_film_url(api_base_url):
    yield f'{api_base_url}/film'


@pytest.fixture(scope='module')
def tst_data_path():
    return ELASTIC_FILM_DATA


def replace_dict_content(src: dict, new_content: dict):
    src.clear()
    src.update(new_content)


@pytest.fixture(scope='module')
def films_from_api_expected(tst_data):
    films = []
    for line in tst_data.split('\n')[1::2]:
        film = json.loads(line)
        film = get_translated_dict(films_es_to_api_mapping, film)
        for genre in film['genre']:
            replace_dict_content(genre, get_translated_dict(genres_es_to_api_mapping, genre))
        for person_kind in ['actors', 'writers', 'directors']:
            for person in film[person_kind]:
                replace_dict_content(person, get_translated_dict(persons_es_to_api_mapping, person))
        films.append(film)
    return films


@pytest.fixture(scope='module')
def films_details_expected(films_from_api_expected):
    films = copy.deepcopy(films_from_api_expected)
    drop_details(films, ['type', 'creation_date'])
    return films


@pytest.fixture(scope='module')
def films_list_expected(films_from_api_expected):
    films = copy.deepcopy(films_from_api_expected)
    drop_details(films, ['type', 'creation_date', 'description', 'genre', 'actors', 'directors', 'writers'])
    return films


@asynccontextmanager
async def _films_index_impl(create_index, cleaner):
    res = await create_index(ELASTIC_FILM_INDEX, ELASTIC_FILM_SCHEMA)
    yield res
    await cleaner(ELASTIC_FILM_INDEX)


@pytest.fixture(scope='class')
async def films_index(create_index, cleaner):
    async with _films_index_impl(create_index, cleaner) as res:
        yield res


@pytest.fixture(scope='class')
async def bulk_films_data(bulk_data_to_es, tst_data, films_index):
    await bulk_data_to_es(tst_data, ELASTIC_FILM_INDEX)


def get_filtered_list(items: list[dict], fields: list[str], value: str) -> list[dict]:
    filtered = filter(lambda item: value in (sub['uuid'] for sub in chain(*[item[field] for field in fields])), items)
    return list(filtered)


def contains_subitem_with_uuid(item: dict, fields: list[str], value: str) -> bool:
    return any(sub['uuid'] == value for sub in chain(*[item[field] for field in fields]))


def all_contain_subitem_with_uuid(items: list[dict], fields: list[str], value: str) -> bool:
    return all(contains_subitem_with_uuid(item, fields, value) for item in items)


def any_contain_subitem_with_uuid(items: list[dict], fields: list[str], value: str) -> bool:
    return any(contains_subitem_with_uuid(item, fields, value) for item in items)


class TestFilm(TestAPIBase):

    filter_fields_map = {
        'genre': ['genre'],
        'person': ['actors', 'directors', 'writers']
    }

    async def test_film_data(
            self, films_index, bulk_films_data, make_get_request, endpoint_film_url, films_list_expected):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
        }

        r = await make_get_request('', endpoint_film_url, params)
        assert r.status == HTTPStatus.OK
        assert len(r.body) == len(films_list_expected)
        assert r.body == films_list_expected

    @pytest.mark.parametrize('params', [{},
                                        {'page[number]': 1},
                                        {'page[size]': 20},
                                        {'page[number]': 3, 'page[size]': 20}])
    async def test_film_query_page_correct(self, films_index, bulk_films_data, make_get_request, endpoint_film_url,
                                           films_list_expected, params):
        r = await make_get_request('', endpoint_film_url, params)
        assert r.status == HTTPStatus.OK

        expected_page_num = params.get('page[number]', 0)
        expected_page_size = params.get('page[size]', 50)
        assert len(r.body) == expected_page_size
        assert r.body == get_page_items(films_list_expected, expected_page_num, expected_page_size)

    async def test_film_query_page_correct_not_found(
            self, films_index, bulk_films_data, make_get_request, endpoint_film_url):
        params = {
            'page[number]': 5,
            'page[size]': 20,
        }

        r = await make_get_request('', endpoint_film_url, params)
        assert r.status == HTTPStatus.NOT_FOUND

    @pytest.mark.parametrize(['page_num', 'page_size'], [(-1, 20), (1, -20), ('foo', 20), (1, 'bar')])
    async def test_film_query_page_incorrect(self, films_index, bulk_films_data, make_get_request,
                                             endpoint_film_url, page_num, page_size):
        params = {
            'page[number]': page_num,
            'page[size]': page_size,
        }

        r = await make_get_request('', endpoint_film_url, params)
        assert r.status == HTTPStatus.UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize(['filter_kind', 'filter_uuid'], [('genre', '86d64c62-926b-4f13-9b27-933342ddb94c'), ])
    async def test_film_query_filter(self, films_index, bulk_films_data, make_get_request, endpoint_film_url,
                                     films_details_expected, filter_kind, filter_uuid):
        filter_fields = self.filter_fields_map[filter_kind]
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            f'filter[{filter_kind}]': filter_uuid
        }

        r = await make_get_request('', endpoint_film_url, params)
        assert r.status == HTTPStatus.OK

        detailed_films = [film for film in films_details_expected if film['uuid'] in get_uuids(r.body)]
        assert all_contain_subitem_with_uuid(detailed_films, filter_fields, filter_uuid)

        dropped_films = [film for film in films_details_expected if film['uuid'] not in get_uuids(r.body)]
        assert not any_contain_subitem_with_uuid(dropped_films, filter_fields, filter_uuid)

    @pytest.mark.parametrize(['filter_kind', 'filter_uuid'], [('genre', '96d64c62-926b-4f13-9b27-933342ddb94d'), ])
    async def test_film_query_filter_not_found(self, films_index, bulk_films_data, make_get_request, endpoint_film_url,
                                               filter_kind, filter_uuid):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            f'filter[{filter_kind}]': filter_uuid
        }

        r = await make_get_request('', endpoint_film_url, params)
        assert r.status == HTTPStatus.NOT_FOUND

    @pytest.mark.parametrize(['filter_kind', 'filter_uuid'], [('genre', 'some_non_uuid'), ])
    async def test_film_query_filter_incorrect(self, films_index, bulk_films_data, make_get_request, endpoint_film_url,
                                               filter_kind, filter_uuid):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            f'filter[{filter_kind}]': filter_uuid
        }

        r = await make_get_request('', endpoint_film_url, params)
        assert r.status == HTTPStatus.UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize(['sort_key', 'desc'], [('title', False), ('title', True),
                                                    ('imdb_rating', False), ('imdb_rating', True)])
    async def test_film_query_sort(self, films_index, bulk_films_data, make_get_request, endpoint_film_url,
                                   films_list_expected, sort_key, desc):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'sort': ('-' if desc else '') + sort_key
        }

        r = await make_get_request('', endpoint_film_url, params)
        assert r.status == HTTPStatus.OK
        assert len(r.body) == len(films_list_expected)
        assert is_sorted(r.body, sort_key, desc)

    @pytest.mark.parametrize(['sort_key', 'desc'], [('unknown', False), ('unknown', True),
                                                    ('un-know-n', False), ('-unknown', True)])
    async def test_film_query_sort_incorrect(self, films_index, bulk_films_data, make_get_request, endpoint_film_url,
                                             films_list_expected, sort_key, desc):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'sort': ('-' if desc else '') + sort_key
        }

        r = await make_get_request('', endpoint_film_url, params)
        assert r.status == HTTPStatus.UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize('query', ['voice', 'war', 'star'])
    async def test_film_query_search(self, films_index, bulk_films_data, make_get_request, endpoint_film_url,
                                     films_details_expected, query):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'query': query
        }

        r = await make_get_request('search', endpoint_film_url, params)
        assert r.status == HTTPStatus.OK

        detailed_films = [film for film in films_details_expected if film['uuid'] in get_uuids(r.body)]
        assert contains_text(detailed_films[0], ['title', 'description'], query)

    async def test_film_query_search_not_found(self, films_index, bulk_films_data, make_get_request, endpoint_film_url):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'query': 'blablabla'
        }

        r = await make_get_request('search', endpoint_film_url, params)
        assert r.status == HTTPStatus.NOT_FOUND

    async def test_film_query_search_incorrect(self, films_index, bulk_films_data, make_get_request, endpoint_film_url):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'query': ''
        }

        r = await make_get_request('search', endpoint_film_url, params)
        assert r.status == HTTPStatus.UNPROCESSABLE_ENTITY


class TestFilmDetails(TestAPIBase):

    async def test_film_details(self, films_index, bulk_films_data, make_get_request, endpoint_film_url,
                                films_details_expected):
        film_uuid = '97141f3e-52f5-421f-813a-08940eeae4b7'
        r = await make_get_request(film_uuid, endpoint_film_url)
        assert r.status == HTTPStatus.OK

        expected = next(film for film in films_details_expected if film['uuid'] == film_uuid)
        assert r.body == expected

    async def test_film_details_not_found(self, films_index, bulk_films_data, make_get_request, endpoint_film_url,
                                          films_details_expected):
        film_uuid = '87141f3e-52f5-421f-813a-08940eeae4b1'
        r = await make_get_request(film_uuid, endpoint_film_url)
        assert r.status == HTTPStatus.NOT_FOUND

    async def test_film_details_incorrect(self, films_index, bulk_films_data, make_get_request, endpoint_film_url,
                                          films_details_expected):
        film_uuid = 'blablabla'
        r = await make_get_request(film_uuid, endpoint_film_url)
        assert r.status == HTTPStatus.UNPROCESSABLE_ENTITY


class TestFilmCache:

    @pytest.fixture(scope='function')
    async def films_index(self, create_index, cleaner):
        async with _films_index_impl(create_index, cleaner) as res:
            yield res

    @pytest.mark.parametrize(['subpath', 'params'], [('', {'page[number]': 1, 'page[size]': 20}),
                                                     ('search', {'page[number]': 0, 'page[size]': 20, 'query': 'war'}),
                                                     ('f5c3a12c-a614-4c1d-baba-05ec0764e7d5', {})])
    async def test_film_cache(self, films_index, create_index, bulk_data_to_es, cleaner, redis_client, make_get_request,
                              endpoint_film_url, tst_data, subpath, params):
        await bulk_data_to_es(tst_data, ELASTIC_FILM_INDEX)
        await redis_client.flushall()

        r = await make_get_request(subpath, endpoint_film_url, params)
        assert r.status == HTTPStatus.OK
        noncached_response = r.body

        await cleaner(ELASTIC_FILM_INDEX)
        await create_index(ELASTIC_FILM_INDEX, ELASTIC_FILM_SCHEMA)

        r = await make_get_request(subpath, endpoint_film_url, params)
        assert r.status == HTTPStatus.OK
        cached_response = r.body
        assert cached_response == noncached_response

        await redis_client.flushall()
        r = await make_get_request(subpath, endpoint_film_url, params)
        assert r.status == HTTPStatus.NOT_FOUND
