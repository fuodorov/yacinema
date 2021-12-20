def test_create_user(client, user_data, users_api):
    resp = client.post(users_api.url, json=user_data)
    assert resp.status_code == 201

    json_data = resp.get_json()
    assert json_data['email'] == user_data['email']
    assert json_data['first_name'] == user_data['first_name']
    assert json_data['last_name'] == user_data['last_name']


def test_create_user_with_existing_email(client, user, users_api):
    resp = client.post(users_api.url, json={
        'email': user['email'],
        'password': 'secret'
    })
    assert resp.status_code == 409


def test_get_user(client, user, users_api):
    url = (users_api / user['uuid']).url
    resp = client.get(url)
    assert resp.status_code == 200
    assert user == resp.get_json()


def test_get_user_with_invalid_uuid(client, users_api):
    users_api /= 'qwerty-123456'
    resp = client.get(users_api.url)
    assert resp.status_code == 400


def test_get_missing_user(client, user, users_api):
    users_api /= user['uuid']
    client.delete(users_api.url)
    resp = client.get(users_api.url)
    assert resp.status_code == 404


def test_delete_user(client, user, users_api):
    users_api /= user['uuid']
    resp = client.delete(users_api.url)
    assert resp.status_code == 204


def test_delete_user_with_invalid_uuid(client, users_api):
    users_api /= 'qwerty-123456'
    resp = client.get(users_api.url)
    assert resp.status_code == 400


def test_delete_missing_user(client, user, users_api):
    users_api /= user['uuid']
    client.delete(users_api.url)
    resp = client.delete(users_api.url)
    assert resp.status_code == 404


def test_change_email(client, user, users_api):
    users_api /= user['uuid']
    new_email = {'email': 'best_email123@example.com'}
    resp = client.patch(users_api.url, json=new_email)
    assert resp.status_code == 200
    assert resp.get_json() == user | new_email


def test_change_first_name(client, user, users_api):
    users_api /= user['uuid']
    new_first_name = {'first_name': 'New first name'}
    resp = client.patch(users_api.url, json=new_first_name)
    assert resp.status_code == 200
    assert resp.get_json() == user | new_first_name


def test_change_last_name(client, user, users_api):
    users_api /= user['uuid']
    new_last_name = {'last_name': 'New last name'}
    resp = client.patch(users_api.url, json=new_last_name)
    assert resp.status_code == 200
    assert resp.get_json() == user | new_last_name


def test_change_password(client, user, user_data, users_api):
    users_api = users_api / user['uuid'] / 'password'
    resp = client.post(users_api.url, json={
        'old_password': user_data['password'],
        'new_password': 'top_secret'
    })
    assert resp.status_code == 200


def test_change_password_with_invalid_old_password(client, user, users_api):
    users_api = users_api / user['uuid'] / 'password'
    resp = client.post(users_api.url, json={
        'old_password': 'top_secret',
        'new_password': 'top_secret'
    })
    assert resp.status_code == 400
