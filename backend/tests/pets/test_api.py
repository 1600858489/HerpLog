async def register_and_login(client, username: str) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "strong-password"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": username, "password": "strong-password"},
    )
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


async def test_create_and_list_unnamed_pet(client) -> None:
    auth_headers = await register_and_login(client, "owner")
    species_response = await client.post(
        "/api/v1/species",
        headers=auth_headers,
        json={"common_name": "豹纹守宫"},
    )
    assert species_response.status_code == 201
    species = species_response.json()["data"]
    response = await client.post(
        "/api/v1/pets",
        headers=auth_headers,
        json={"species_uuid": species["uuid"]},
    )
    assert response.status_code == 201
    pet = response.json()["data"]
    assert pet["name"] is None
    assert pet["pet_code"]
    assert "id" not in pet
    assert "user_id" not in pet
    assert "password_hash" not in pet


async def test_pet_list_is_paginated(client) -> None:
    auth_headers = await register_and_login(client, "owner")
    response = await client.get(
        "/api/v1/pets?page=1&page_size=20",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["page"] == 1
    assert "items" in response.json()["data"]
