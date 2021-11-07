import copy
import json
import pytest
from contextlib import asynccontextmanager
from http import HTTPStatus

from settings import ELASTIC_PERSON_INDEX, ELASTIC_PERSON_DATA, ELASTIC_PERSON_SCHEMA
from utils.lists import drop_details, get_uuids, get_page_items, is_sorted
from utils.mappings import persons_es_to_api_mapping, get_translated_dict
from utils.objects import contains_text
from utils.tests import TestAPIBase


pytestmark = pytest.mark.asyncio


@pytest.fixture(scope='session')
def endpoint_person_url(api_base_url):
    yield f'{api_base_url}/person'


@pytest.fixture(scope='module')
def tst_data_path():
    return ELASTIC_PERSON_DATA


@pytest.fixture(scope='module')
def persons_from_api_expected(tst_data):
    persons = []
    for line in tst_data.split('\n')[1::2]:
        person = json.loads(line)
        person = get_translated_dict(persons_es_to_api_mapping, person)
        persons.append(person)
    return persons


@pytest.fixture(scope='module')
def persons_details_expected(persons_from_api_expected):
    return copy.deepcopy(persons_from_api_expected)


@pytest.fixture(scope='module')
def persons_list_expected(persons_from_api_expected):
    persons = copy.deepcopy(persons_from_api_expected)
    drop_details(persons, ['roles', 'films'])
    return persons


@asynccontextmanager
async def _persons_index_impl(create_index, cleaner):
    res = await create_index(ELASTIC_PERSON_INDEX, ELASTIC_PERSON_SCHEMA)
    yield res
    await cleaner(ELASTIC_PERSON_INDEX)


@pytest.fixture(scope='class')
async def persons_index(create_index, cleaner):
    async with _persons_index_impl(create_index, cleaner) as res:
        yield res


@pytest.fixture(scope='class')
async def bulk_persons_data(bulk_data_to_es, tst_data, persons_index):
    await bulk_data_to_es(tst_data, ELASTIC_PERSON_INDEX)


class TestPerson(TestAPIBase):

    async def test_person_data(
            self, persons_index, bulk_persons_data, make_get_request, endpoint_person_url, persons_list_expected):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
        }

        r = await make_get_request('', endpoint_person_url, params)
        assert r.status == HTTPStatus.OK
        assert len(r.body) == len(persons_list_expected)
        assert r.body == persons_list_expected

    @pytest.mark.parametrize('params', [{},
                                        {'page[number]': 0},
                                        {'page[size]': 10},
                                        {'page[number]': 1, 'page[size]': 1}])
    async def test_person_query_page_correct(self, persons_index, bulk_persons_data, make_get_request,
                                             endpoint_person_url, persons_list_expected, params):
        r = await make_get_request('', endpoint_person_url, params)
        assert r.status == HTTPStatus.OK

        expected_page_num = params.get('page[number]', 0)
        expected_page_size = params.get('page[size]', 50)
        assert len(r.body) <= expected_page_size
        assert r.body == get_page_items(persons_list_expected, expected_page_num, expected_page_size)

    async def test_person_query_page_correct_not_found(
            self, persons_index, bulk_persons_data, make_get_request, endpoint_person_url):
        params = {
            'page[number]': 3,
            'page[size]': 10,
        }

        r = await make_get_request('', endpoint_person_url, params)
        assert r.status == HTTPStatus.NOT_FOUND

    @pytest.mark.parametrize(['page_num', 'page_size'], [(-1, 20), (1, -20), ('foo', 20), (1, 'bar')])
    async def test_person_query_page_incorrect(self, persons_index, bulk_persons_data, make_get_request,
                                               endpoint_person_url, page_num, page_size):
        params = {
            'page[number]': page_num,
            'page[size]': page_size,
        }

        r = await make_get_request('', endpoint_person_url, params)
        assert r.status == HTTPStatus.UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize(['sort_key', 'desc'], [('full_name', False), ('full_name', True)])
    async def test_person_query_sort(self, persons_index, bulk_persons_data, make_get_request, endpoint_person_url,
                                     persons_list_expected, sort_key, desc):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'sort': ('-' if desc else '') + sort_key
        }

        r = await make_get_request('', endpoint_person_url, params)
        assert r.status == HTTPStatus.OK
        assert len(r.body) == len(persons_list_expected)
        assert is_sorted(r.body, sort_key, desc)

    @pytest.mark.parametrize(['sort_key', 'desc'], [('unknown', False), ('unknown', True),
                                                    ('un-know-n', False), ('-unknown', True)])
    async def test_person_query_sort_incorrect(self, persons_index, bulk_persons_data, make_get_request,
                                               endpoint_person_url, persons_list_expected, sort_key, desc):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'sort': ('-' if desc else '') + sort_key
        }

        r = await make_get_request('', endpoint_person_url, params)
        assert r.status == HTTPStatus.UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize('query', ['Mark', 'Harrison'])
    async def test_person_query_search(self, persons_index, bulk_persons_data, make_get_request, endpoint_person_url,
                                       persons_details_expected, query):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'query': query
        }

        r = await make_get_request('search', endpoint_person_url, params)
        assert r.status == HTTPStatus.OK

        detailed_persons = [person for person in persons_details_expected if person['uuid'] in get_uuids(r.body)]
        assert contains_text(detailed_persons[0], ['full_name'], query)

    async def test_person_query_search_not_found(self, persons_index, bulk_persons_data, make_get_request,
                                                 endpoint_person_url):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'query': 'blablabla'
        }

        r = await make_get_request('search', endpoint_person_url, params)
        assert r.status == HTTPStatus.NOT_FOUND

    async def test_person_query_search_incorrect(self, persons_index, bulk_persons_data, make_get_request,
                                                 endpoint_person_url):
        params = {
            'page[number]': 0,
            'page[size]': 9999,
            'query': ''
        }

        r = await make_get_request('search', endpoint_person_url, params)
        assert r.status == HTTPStatus.UNPROCESSABLE_ENTITY


class TestPersonDetails(TestAPIBase):

    async def test_person_details(self, persons_index, bulk_persons_data, make_get_request, endpoint_person_url,
                                  persons_details_expected):
        person_uuid = '6068f16b-9b33-4cb1-a477-81c334ff9542'
        r = await make_get_request(person_uuid, endpoint_person_url)
        assert r.status == HTTPStatus.OK

    async def test_person_details_not_found(self, persons_index, bulk_persons_data, make_get_request,
                                            endpoint_person_url, persons_details_expected):
        person_uuid = '21d53e36-b761-4f61-b054-8523be7493c1'
        r = await make_get_request(person_uuid, endpoint_person_url)
        assert r.status == HTTPStatus.NOT_FOUND

    async def test_person_details_incorrect(self, persons_index, bulk_persons_data, make_get_request,
                                            endpoint_person_url, persons_details_expected):
        person_uuid = 'blablabla'
        r = await make_get_request(person_uuid, endpoint_person_url)
        assert r.status == HTTPStatus.UNPROCESSABLE_ENTITY


class TestPersonCache:

    @pytest.fixture(scope='function')
    async def persons_index(self, create_index, cleaner):
        async with _persons_index_impl(create_index, cleaner) as res:
            yield res

    @pytest.mark.parametrize(['subpath', 'params'], [('', {'page[number]': 1, 'page[size]': 1}),
                                                     ('search', {'page[number]': 0, 'page[size]': 1, 'query': 'Mark'}),
                                                     ('6068f16b-9b33-4cb1-a477-81c334ff9542', {})])
    async def test_person_cache(self, persons_index, create_index, bulk_data_to_es, cleaner, redis_client,
                                make_get_request, endpoint_person_url, tst_data, subpath, params):
        await bulk_data_to_es(tst_data, ELASTIC_PERSON_INDEX)
        await redis_client.flushall()

        r = await make_get_request(subpath, endpoint_person_url, params)
        assert r.status == HTTPStatus.OK
        noncached_response = r.body

        await cleaner(ELASTIC_PERSON_INDEX)
        await create_index(ELASTIC_PERSON_INDEX, ELASTIC_PERSON_SCHEMA)

        r = await make_get_request(subpath, endpoint_person_url, params)
        assert r.status == HTTPStatus.OK
        cached_response = r.body
        assert cached_response == noncached_response

        await redis_client.flushall()
        r = await make_get_request(subpath, endpoint_person_url, params)
        assert r.status == HTTPStatus.NOT_FOUND
