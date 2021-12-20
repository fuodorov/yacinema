import os
import pytest
from mimesis import Person
from furl import furl

from app import app, create_app, db


DATABASE_TEST_URI = 'postgresql://{username}:{password}@{host}:{port}/{database_name}'.format(
    username=os.environ.get('POSTGRES_USER'), password=os.environ.get('POSTGRES_PASSWORD'),
    host=os.environ.get('POSTGRES_AUTH_HOST'), port=os.environ.get('POSTGRES_AUTH_PORT'),
    database_name='testdb'
)


@pytest.fixture(scope='session')
def client():
    with app.test_client() as client:
        app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_TEST_URI
        with app.app_context():
            create_app()
            yield client


@pytest.fixture(autouse=True)
def database_pg():
    db.create_all()
    yield
    db.session.remove()
    db.drop_all()


@pytest.fixture
def user_data() -> dict:
    person = Person('en')
    return {
        'email': person.email(),
        'first_name': person.first_name(),
        'last_name': person.last_name(),
        'password': person.password()
    }


@pytest.fixture
def users_api() -> furl:
    return furl('/auth/v1/users')


@pytest.fixture
def user(client, user_data, users_api) -> dict:
    resp = client.post(users_api.url, json=user_data)
    user = resp.get_json()
    yield user
    client.delete((users_api / user['uuid']).url)


@pytest.fixture
def auth_api() -> furl:
    return furl('/auth/v1/auth_token')


@pytest.fixture
def auth_user(client, user, user_data, auth_api) -> dict:
    resp = client.post(auth_api.url, json={'email': user['email'], 'password': user_data['password']})
    tokens = resp.get_json()
    yield tokens
    client.delete(auth_api.url, headers={'Authorization': f"Bearer {tokens['access_token']}"})
