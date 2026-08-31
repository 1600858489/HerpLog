async def test_register_returns_public_user_only(client) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "keeper", "password": "strong-password"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["username"] == "keeper"
    assert "id" not in body["data"]
    assert "password_hash" not in body["data"]


async def test_login_refresh_logout_and_me_flow(client) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"username": "keeper", "password": "strong-password"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "keeper", "password": "strong-password", "device_info": "test"},
    )
    assert login.status_code == 200
    auth = login.json()["data"]
    assert auth["token_type"] == "bearer"
    assert "id" not in auth["user"]

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {auth['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["data"]["username"] == "keeper"

    refreshed = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": auth["refresh_token"]},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["data"]["refresh_token"] != auth["refresh_token"]

    logout = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refreshed.json()["data"]["refresh_token"]},
    )
    assert logout.status_code == 200
    assert logout.json() == {"code": 0, "message": "success", "data": None}


from datetime import timedelta

from backend.app.core.security.jwt import create_access_token


async def test_refresh_token_cannot_be_reused_after_rotation(client) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"username": "keeper", "password": "strong-password"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "keeper", "password": "strong-password"},
    )
    old_refresh_token = login.json()["data"]["refresh_token"]
    await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    reused = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert reused.status_code == 401
    assert reused.json()["code"] == 2211


async def test_missing_bearer_token_returns_safe_401(client) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["message"] == "请先登录"


async def test_expired_access_token_returns_safe_401(client) -> None:
    expired_token = create_access_token(
        "00000000-0000-0000-0000-000000000000",
        expires_delta=timedelta(seconds=-1),
    )
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == 1030
    assert "Traceback" not in response.text


async def test_auth_api_rejects_internal_id_and_hides_authentication_details(client) -> None:
    invalid = await client.post(
        "/api/v1/auth/register",
        json={"username": "keeper", "password": "strong-password", "id": 1},
    )
    assert invalid.status_code == 422
    assert '"id"' not in invalid.text

    failed = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "missing", "password": "wrong-pass"},
    )
    assert failed.status_code == 401
    assert failed.json()["code"] == 2201
    assert failed.json()["message"] == "用户名或密码错误"
