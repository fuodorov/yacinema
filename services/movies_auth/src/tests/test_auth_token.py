def test_login(client, user, user_data, auth_api):
    resp = client.post(auth_api.url, json={'email': user['email'], 'password': user_data['password']})
    assert resp.status_code == 200
    assert 'access_token' in resp.get_json()
    assert 'refresh_token' in resp.get_json()


def test_login_with_invalid_password(client, user, user_data, auth_api):
    resp = client.post(auth_api.url, json={'email': user['email'], 'password': 'qwerty'})
    assert resp.status_code == 409


def test_logout(client, auth_user, auth_api):
    resp = client.delete(auth_api.url, headers={'Authorization': f"Bearer {auth_user['access_token']}"})
    assert resp.status_code == 204


def test_logout_all(client, auth_user, auth_api):
    auth_api /= 'all'
    resp = client.delete(auth_api.url, headers={'Authorization': f"Bearer {auth_user['access_token']}"})
    assert resp.status_code == 204


def test_refresh(client, auth_user, auth_api):
    auth_api /= 'token_refresh'
    resp = client.post(auth_api.url, headers={'Authorization': f"Bearer {auth_user['refresh_token']}"})
    assert resp.status_code == 200
    assert 'access_token' in resp.get_json()
    assert 'refresh_token' in resp.get_json()
