import pytest
from mimesis import Text
from furl import furl


@pytest.fixture
def permission_data() -> dict:
    text = Text('en')
    return {
        'name': f'{text.word()}_{text.word()}',
        'description': text.sentence()
    }


@pytest.fixture
def role_data() -> dict:
    text = Text('en')
    return {
        'name': f'{text.word()}',
        'description': text.sentence()
    }


@pytest.fixture
def permissions_api() -> furl:
    return furl('/api/v1/permissions')


@pytest.fixture
def roles_api() -> furl:
    return furl('/api/v1/roles')


@pytest.fixture
def role(client, role_data, roles_api):
    resp = client.post(roles_api.url, json=role_data)
    role = resp.get_json()
    return role


@pytest.fixture
def permission(client, permission_data, permissions_api):
    resp = client.post(permissions_api.url, json=permission_data)
    permission = resp.get_json()
    return permission


@pytest.fixture
def role_with_permission(client, role, permission, roles_api):
    api_url = roles_api / role['name']
    resp = client.post((api_url / 'permissions').url, json={'name': permission['name']})
    role['permissions'] = resp.get_json()
    return role


@pytest.fixture
def user_with_role(client, role_with_permission, user, users_api):
    api_url = users_api / user['uuid']
    resp = client.post((api_url / 'roles').url, json={'name': role_with_permission['name']})
    user['roles'] = resp.get_json()
    return user


def test_create_role(client, role_data, roles_api):
    resp = client.post(roles_api.url, json=role_data)
    assert resp.status_code == 201

    json_data = resp.get_json()
    assert json_data['name'] == role_data['name']
    assert json_data['description'] == role_data['description']
    assert json_data['permissions'] == []


def test_create_role_with_existing_name(client, role, roles_api):
    resp = client.post(roles_api.url, json={
        'name': role['name'],
        'description': 'some description'
    })
    assert resp.status_code == 409


def test_create_role_without_name(client, role_data, roles_api):
    resp = client.post(roles_api.url, json={'description': role_data['description']})
    assert resp.status_code == 400


def test_get_role(client, role, roles_api):
    url = (roles_api / role['name']).url
    resp = client.get(url)
    assert resp.status_code == 200
    assert resp.get_json() == role


def test_get_role_with_invalid_name(client, roles_api):
    url = (roles_api / 'some_nonexisting_role_name').url
    resp = client.get(url)
    assert resp.status_code == 404


def test_delete_role(client, role, roles_api):
    roles_api /= role['name']
    resp = client.delete(roles_api.url)
    assert resp.status_code == 204


def test_delete_nonexisting_role(client, roles_api):
    roles_api /= 'some_nonexisting_role_name'
    resp = client.delete(roles_api.url)
    assert resp.status_code == 404


def test_change_role(client, role, roles_api):
    roles_api /= role['name']
    new_details = {'description': 'new description'}
    resp = client.patch(roles_api.url, json=new_details)
    assert resp.status_code == 200
    assert resp.get_json() == role | new_details


def test_create_permission(client, permission_data, permissions_api):
    resp = client.post(permissions_api.url, json=permission_data)
    assert resp.status_code == 201

    json_data = resp.get_json()
    assert json_data['name'] == permission_data['name']
    assert json_data['description'] == permission_data['description']


def test_get_permissions(client, permission, permissions_api):
    resp = client.get(permissions_api.url)
    assert resp.status_code == 200
    assert resp.get_json() == [permission]


def test_delete_permission(client, permission, permissions_api):
    permissions_api /= permission['name']
    resp = client.delete(permissions_api.url)
    assert resp.status_code == 204


def test_delete_nonexisting_permission(client, permissions_api):
    permissions_api /= 'nonexisting_permission_name'
    resp = client.delete(permissions_api.url)
    assert resp.status_code == 404


def test_add_permission_to_role(client, permission, role, roles_api):
    roles_api = roles_api / role['name'] / 'permissions'
    resp = client.post(roles_api.url, json={'name': permission['name']})
    assert resp.status_code == 200
    assert resp.get_json() == [permission]


def test_remove_permission_from_role(client, role_with_permission, permission, roles_api):
    roles_api = roles_api / role_with_permission['name'] / 'permissions' / permission['name']
    resp = client.delete(roles_api.url)
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_add_role_to_user(client, role_with_permission, user, users_api):
    users_api = users_api / user['uuid'] / 'roles'
    resp = client.post(users_api.url, json={'name': role_with_permission['name']})
    assert resp.status_code == 200
    assert resp.get_json() == [role_with_permission]


def test_remove_role_from_user(client, user_with_role, role, users_api):
    users_api = users_api / user_with_role['uuid'] / 'roles' / role['name']
    resp = client.delete(users_api.url)
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_user_combined_permissions(client, user_with_role, permission, users_api):
    combined_permissions_api = users_api / user_with_role['uuid'] / 'combined_permissions'
    resp = client.get(combined_permissions_api.url)
    assert resp.status_code == 200
    assert resp.get_json() == user_with_role['roles'][0]['permissions']

    permissions_api = users_api / user_with_role['uuid'] / 'permissions'
    resp = client.get(permissions_api.url)
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_user_combined_permissions_validation(client, user_with_role, permission, users_api):
    validation_api = users_api / user_with_role['uuid'] / 'combined_permissions' / 'validation'
    resp = client.get(validation_api.url, query_string={
        'permissions': '{{"any":["some_other_permission_name", "{}"]}}'.format(permission['name'])
    })
    assert resp.status_code == 200
    assert resp.get_json()['valid'] == True
