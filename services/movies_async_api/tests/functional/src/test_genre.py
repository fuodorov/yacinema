import copy
import json
import pytest
from contextlib import asynccontextmanager
from http import HTTPStatus

from settings import ELASTIC_GENRE_INDEX, ELASTIC_GENRE_DATA, ELASTIC_GENRE_SCHEMA
from utils.lists import drop_details, get_uuids, get_page_items, is_sorted
from utils.mappings import genres_es_to_api_mapping, get_translated_dict
from utils.objects import contains_text
from utils.tests import TestAPIBase


pytestmark = pytest.mark.asyncio


@pytest.fixture(scope='session')
def endpoint_genre_url(api_base_url):
    yield f'{api_base_url}/genre'


@pytest.fixture(scope='module')
def tst_data_path():
    return ELASTIC_GENRE_DATA


@pytest.fixture(scope='module')
def genres_from_api_expected(tst_data):
    genres = []
    for line in tst_data.split('\n')[1::2]:
        genre = json.loads(line)
        genre = get_translated_dict(genres_es_to_api_mapping, genre)
        genres.append(genre)
    return genres


@pytest.fixture(scope='module')
def genres_details_expected(genres_from_api_expected):
    return copy.deepcopy(genres_from_api_expected)


@pytest.fixture(scope='module')
def genres_list_expected(genres_from_api_expected):
    genres = copy.deepcopy(genres_from_api_expected)
    drop_details(genres, ['description'])
    return genres


@asynccontextmanager
async def _genres_index_impl(create_index, cleaner):
    res = await create_index(ELASTIC_GENRE_INDEX, ELASTIC_GENRE_SCHEMA)
    yield res
    await cleaner(ELASTIC_GENRE_INDEX)


@pytest.fixture(scope='class')
async def genres_index(create_index, cleaner):
    async with _genres_index_impl(create_index, cleaner) as res:
        yield res


@pytest.fixture(scope='class')
async def bulk_genres_data(bulk_data_to_es, tst_data, genres_index):
    await bulk_data_to_es(tst_data, ELASTIC_GENRE_INDEX)


class TestGenre(TestAPIBase):

    async def test_genre_data(
            self, genres_index, bulk_genres_data, make_get_request, endpoint_genre_url, genres_list_expected):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
        }

        r = await make_get_request('', endpoint_genre_url, params)
        assert r.status == HTTPStatus.OK
        assert len(r.body) == len(genres_list_expected)
        assert r.body == genres_list_expected

    @pytest.mark.parametrize(['page_num', 'page_size'], [(None, None), (0, None), (None, 10), (1, 10)])
    async def test_genre_query_page_correct(self, genres_index, bulk_genres_data, make_get_request, endpoint_genre_url,
                                            genres_list_expected, page_num, page_size):
        params = {}
        if page_num:
            params['page[number]'] = page_num
        if page_size:
            params['page[size]'] = page_size

        r = await make_get_request('', endpoint_genre_url, params)
        assert r.status == HTTPStatus.OK

        expected_page_num = page_num or 0
        expected_page_size = page_size or 50
        assert len(r.body) <= expected_page_size
        assert r.body == get_page_items(genres_list_expected, expected_page_num, expected_page_size)

    async def test_genre_query_page_correct_not_found(
            self, genres_index, bulk_genres_data, make_get_request, endpoint_genre_url):
        params = {
            'page[number]': 3,
            'page[size]': 10,
        }

        r = await make_get_request('', endpoint_genre_url, params)
        assert r.status == HTTPStatus.NOT_FOUND

    @pytest.mark.parametrize(['page_num', 'page_size'], [(-1, 20), (1, -20), ('foo', 20), (1, 'bar')])
    async def test_genre_query_page_incorrect(self, genres_index, bulk_genres_data, make_get_request,
                                              endpoint_genre_url, page_num, page_size):
        params = {
            'page[number]': page_num,
            'page[size]': page_size,
        }

        r = await make_get_request('', endpoint_genre_url, params)
        assert r.status == HTTPStatus.UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize(['sort_key', 'desc'], [('name', False), ('name', True)])
    async def test_genre_query_sort(self, genres_index, bulk_genres_data, make_get_request, endpoint_genre_url,
                                    genres_list_expected, sort_key, desc):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'sort': ('-' if desc else '') + sort_key
        }

        r = await make_get_request('', endpoint_genre_url, params)
        assert r.status == HTTPStatus.OK
        assert len(r.body) == len(genres_list_expected)
        assert is_sorted(r.body, sort_key, desc)

    @pytest.mark.parametrize(['sort_key', 'desc'], [('unknown', False), ('unknown', True),
                                                    ('un-know-n', False), ('-unknown', True)])
    async def test_genre_query_sort_incorrect(self, genres_index, bulk_genres_data, make_get_request,
                                              endpoint_genre_url, genres_list_expected, sort_key, desc):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'sort': ('-' if desc else '') + sort_key
        }

        r = await make_get_request('', endpoint_genre_url, params)
        assert r.status == HTTPStatus.UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize('query', ['comedy', 'show'])
    async def test_genre_query_search(self, genres_index, bulk_genres_data, make_get_request, endpoint_genre_url,
                                      genres_details_expected, query):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'query': query
        }

        r = await make_get_request('search', endpoint_genre_url, params)
        assert r.status == HTTPStatus.OK

        detailed_genres = [genre for genre in genres_details_expected if genre['uuid'] in get_uuids(r.body)]
        assert contains_text(detailed_genres[0], ['name', 'description'], query)

    async def test_genre_query_search_not_found(self, genres_index, bulk_genres_data, make_get_request,
                                                endpoint_genre_url):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'query': 'blablabla'
        }

        r = await make_get_request('search', endpoint_genre_url, params)
        assert r.status == HTTPStatus.NOT_FOUND

    async def test_genre_query_search_incorrect(self, genres_index, bulk_genres_data, make_get_request,
                                                endpoint_genre_url):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'query': ''
        }

        r = await make_get_request('search', endpoint_genre_url, params)
        assert r.status == HTTPStatus.UNPROCESSABLE_ENTITY


class TestGenreDetails(TestAPIBase):

    async def test_genre_details(self, genres_index, bulk_genres_data, make_get_request, endpoint_genre_url,
                                 genres_details_expected):
        genre_uuid = '11d53e36-b761-4f61-b054-8523be7493c0'
        r = await make_get_request(genre_uuid, endpoint_genre_url)
        assert r.status == HTTPStatus.OK

        expected = next(genre for genre in genres_details_expected if genre['uuid'] == genre_uuid)
        assert r.body == expected

    async def test_genre_details_not_found(self, genres_index, bulk_genres_data, make_get_request, endpoint_genre_url,
                                           genres_details_expected):
        genre_uuid = '21d53e36-b761-4f61-b054-8523be7493c1'
        r = await make_get_request(genre_uuid, endpoint_genre_url)
        assert r.status == HTTPStatus.NOT_FOUND

    async def test_genre_details_incorrect(self, genres_index, bulk_genres_data, make_get_request, endpoint_genre_url,
                                           genres_details_expected):
        genre_uuid = 'blablabla'
        r = await make_get_request(genre_uuid, endpoint_genre_url)
        assert r.status == HTTPStatus.UNPROCESSABLE_ENTITY


class TestGenreCache:

    @pytest.fixture(scope='function')
    async def genres_index(self, create_index, cleaner):
        async with _genres_index_impl(create_index, cleaner) as res:
            yield res

    @pytest.mark.parametrize(['subpath', 'params'], [('', {'page[number]': 1, 'page[size]': 10}),
                                                     ('search', {'page[number]': 0, 'page[size]': 10, 'query': 'show'}),
                                                     ('c3158794-bdb7-4524-9909-8afa912396de', {})])
    async def test_genre_cache(self, genres_index, create_index, bulk_data_to_es, cleaner, redis_client,
                               make_get_request, endpoint_genre_url, tst_data, subpath, params):
        await bulk_data_to_es(tst_data, ELASTIC_GENRE_INDEX)
        await redis_client.flushall()

        r = await make_get_request(subpath, endpoint_genre_url, params)
        assert r.status == HTTPStatus.OK
        noncached_response = r.body

        await cleaner(ELASTIC_GENRE_INDEX)
        await create_index(ELASTIC_GENRE_INDEX, ELASTIC_GENRE_SCHEMA)

        r = await make_get_request(subpath, endpoint_genre_url, params)
        assert r.status == HTTPStatus.OK
        cached_response = r.body
        assert cached_response == noncached_response

        await redis_client.flushall()
        r = await make_get_request(subpath, endpoint_genre_url, params)
        assert r.status == HTTPStatus.NOT_FOUND
