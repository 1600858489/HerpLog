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


async def test_pet_can_be_updated_and_soft_deleted(client) -> None:
    auth_headers = await register_and_login(client, "owner")
    species = (
        await client.post("/api/v1/species", headers=auth_headers, json={"common_name": "龟"})
    ).json()["data"]
    pet = (
        await client.post(
            "/api/v1/pets",
            headers=auth_headers,
            json={"species_uuid": species["uuid"]},
        )
    ).json()["data"]

    updated = await client.patch(
        f"/api/v1/pets/{pet['uuid']}",
        headers=auth_headers,
        json={"name": "小绿"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "小绿"

    deleted = await client.delete(f"/api/v1/pets/{pet['uuid']}", headers=auth_headers)
    assert deleted.status_code == 200
    hidden = await client.get(f"/api/v1/pets/{pet['uuid']}", headers=auth_headers)
    assert hidden.status_code == 404


async def test_species_supports_list_update_and_delete(client) -> None:
    auth_headers = await register_and_login(client, "owner")
    created = await client.post(
        "/api/v1/species", headers=auth_headers, json={"common_name": "龟"}
    )
    species_uuid = created.json()["data"]["uuid"]

    listed = await client.get("/api/v1/species", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()["data"]["items"][0]["common_name"] == "龟"

    updated = await client.patch(
        f"/api/v1/species/{species_uuid}",
        headers=auth_headers,
        json={"common_name": "陆龟"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["common_name"] == "陆龟"

    deleted = await client.delete(f"/api/v1/species/{species_uuid}", headers=auth_headers)
    assert deleted.status_code == 200
    assert (await client.get("/api/v1/species", headers=auth_headers)).json()["data"]["total"] == 0


async def test_management_assignment_history_can_be_created_and_removed(client) -> None:
    auth_headers = await register_and_login(client, "owner")
    species = (
        await client.post("/api/v1/species", headers=auth_headers, json={"common_name": "龟"})
    ).json()["data"]
    pet = (
        await client.post(
            "/api/v1/pets", headers=auth_headers, json={"species_uuid": species["uuid"]}
        )
    ).json()["data"]
    unit_type = (
        await client.post(
            "/api/v1/management-unit-types",
            headers=auth_headers,
            json={"name": "龟池"},
        )
    ).json()["data"]
    unit = (
        await client.post(
            "/api/v1/management-units",
            headers=auth_headers,
            json={"type_uuid": unit_type["uuid"], "unit_code": "POOL-001"},
        )
    ).json()["data"]

    assignment = await client.post(
        f"/api/v1/pets/{pet['uuid']}/management-assignments",
        headers=auth_headers,
        json={"management_unit_uuid": unit["uuid"], "started_at": "2026-01-01T00:00:00Z"},
    )
    assert assignment.status_code == 201
    history = await client.get(
        f"/api/v1/pets/{pet['uuid']}/management-assignments", headers=auth_headers
    )
    assert history.status_code == 200
    assert history.json()["data"]["total"] == 1

    removed = await client.post(
        f"/api/v1/pets/{pet['uuid']}/management-assignments/remove",
        headers=auth_headers,
        json={"ended_at": "2026-02-01T00:00:00Z"},
    )
    assert removed.status_code == 200
    assert (await client.get(f"/api/v1/pets/{pet['uuid']}", headers=auth_headers)).status_code == 200


async def test_patch_endpoints_allow_partial_updates(client) -> None:
    auth_headers = await register_and_login(client, "owner")
    species = (
        await client.post("/api/v1/species", headers=auth_headers, json={"common_name": "龟"})
    ).json()["data"]
    species_update = await client.patch(
        f"/api/v1/species/{species['uuid']}",
        headers=auth_headers,
        json={"note": "陆栖"},
    )
    assert species_update.status_code == 200
    assert species_update.json()["data"]["note"] == "陆栖"

    gene = (
        await client.post("/api/v1/genes", headers=auth_headers, json={"name": "豹纹"})
    ).json()["data"]
    gene_update = await client.patch(
        f"/api/v1/genes/{gene['uuid']}",
        headers=auth_headers,
        json={"note": "显性表现"},
    )
    assert gene_update.status_code == 200
    assert gene_update.json()["data"]["note"] == "显性表现"


async def test_invalid_pet_domain_enums_are_rejected(client) -> None:
    auth_headers = await register_and_login(client, "owner")
    species = (
        await client.post("/api/v1/species", headers=auth_headers, json={"common_name": "龟"})
    ).json()["data"]
    pet = await client.post(
        "/api/v1/pets",
        headers=auth_headers,
        json={"species_uuid": species["uuid"], "sex": "invalid"},
    )
    gene = await client.post(
        "/api/v1/genes",
        headers=auth_headers,
        json={"name": "豹纹", "inheritance_mode": "invalid"},
    )
    origin = await client.post(
        f"/api/v1/pets/00000000-0000-0000-0000-000000000001/origins",
        headers=auth_headers,
        json={"origin_type": "invalid"},
    )
    assert pet.status_code == 422
    assert gene.status_code == 422
    assert origin.status_code == 422


async def test_duplicate_gene_and_tag_return_conflict(client) -> None:
    auth_headers = await register_and_login(client, "owner")
    first_gene = await client.post("/api/v1/genes", headers=auth_headers, json={"name": "豹纹"})
    second_gene = await client.post("/api/v1/genes", headers=auth_headers, json={"name": "豹纹"})
    first_tag = await client.post(
        "/api/v1/identification-tags", headers=auth_headers, json={"name": "尾端缺口"}
    )
    second_tag = await client.post(
        "/api/v1/identification-tags", headers=auth_headers, json={"name": "尾端缺口"}
    )
    assert first_gene.status_code == 201
    assert second_gene.status_code == 409
    assert first_tag.status_code == 201
    assert second_tag.status_code == 409


async def test_other_user_cannot_read_private_pet(client) -> None:
    owner_headers = await register_and_login(client, "owner")
    other_headers = await register_and_login(client, "other")
    species = (
        await client.post("/api/v1/species", headers=owner_headers, json={"common_name": "龟"})
    ).json()["data"]
    pet = (
        await client.post(
            "/api/v1/pets", headers=owner_headers, json={"species_uuid": species["uuid"]}
        )
    ).json()["data"]

    response = await client.get(f"/api/v1/pets/{pet['uuid']}", headers=other_headers)
    assert response.status_code == 404
    assert response.json()["code"] == 3101


async def test_pet_request_rejects_internal_fields(client) -> None:
    auth_headers = await register_and_login(client, "owner")
    response = await client.post(
        "/api/v1/pets",
        headers=auth_headers,
        json={
            "species_uuid": "00000000-0000-0000-0000-000000000001",
            "id": 1,
            "user_id": 1,
        },
    )
    assert response.status_code == 422
    assert "password_hash" not in response.text
    assert "Traceback" not in response.text


async def test_origin_partial_update_preserves_parent_reference(client) -> None:
    auth_headers = await register_and_login(client, "owner")
    species = (
        await client.post("/api/v1/species", headers=auth_headers, json={"common_name": "龟"})
    ).json()["data"]
    parent = (
        await client.post(
            "/api/v1/pets", headers=auth_headers, json={"species_uuid": species["uuid"]}
        )
    ).json()["data"]
    pet = (
        await client.post(
            "/api/v1/pets", headers=auth_headers, json={"species_uuid": species["uuid"]}
        )
    ).json()["data"]
    origin = (
        await client.post(
            f"/api/v1/pets/{pet['uuid']}/origins",
            headers=auth_headers,
            json={"origin_type": "self_bred", "parent_pet_uuid": parent["uuid"]},
        )
    ).json()["data"]

    updated = await client.patch(
        f"/api/v1/pets/{pet['uuid']}/origins/{origin['uuid']}",
        headers=auth_headers,
        json={"note": "已核验"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["parent_pet_uuid"] == parent["uuid"]


async def test_life_stage_and_origin_can_be_recorded(client) -> None:
    auth_headers = await register_and_login(client, "owner")
    species = (
        await client.post("/api/v1/species", headers=auth_headers, json={"common_name": "龟"})
    ).json()["data"]
    pet = (
        await client.post(
            "/api/v1/pets", headers=auth_headers, json={"species_uuid": species["uuid"]}
        )
    ).json()["data"]

    stage = await client.post(
        f"/api/v1/pets/{pet['uuid']}/life-stages",
        headers=auth_headers,
        json={"stage": "幼体", "started_at": "2026-01-01T00:00:00Z"},
    )
    assert stage.status_code == 201
    origin = await client.post(
        f"/api/v1/pets/{pet['uuid']}/origins",
        headers=auth_headers,
        json={"origin_type": "purchased", "external_name": "本地爬宠店"},
    )
    assert origin.status_code == 201
    detail = await client.get(f"/api/v1/pets/{pet['uuid']}", headers=auth_headers)
    assert detail.status_code == 200
    assert len(detail.json()["data"]["life_stages"]) == 1
    assert len(detail.json()["data"]["origins"]) == 1
