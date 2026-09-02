from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from ...core.pagination import PaginationData, PaginationParams, build_pagination
from ...core.response import ResponseEnvelope, success_response
from ...schemas.pets import (
    GeneCreateRequest,
    GeneResponse,
    GeneUpdateRequest,
    SpeciesCreateRequest,
    SpeciesResponse,
    SpeciesUpdateRequest,
    TagCreateRequest,
    TagResponse,
    TagUpdateRequest,
)
from ...selectors import list_genes, list_species, list_tags
from ...services import (
    create_gene,
    create_species,
    create_tag,
    soft_delete_gene,
    soft_delete_species,
    soft_delete_tag,
    update_gene,
    update_species,
    update_tag,
)
from .common import CurrentUser, DbSession


classification_router = APIRouter()


@classification_router.get(
    "/species", response_model=ResponseEnvelope[PaginationData[SpeciesResponse]]
)
async def list_species_view(
    current_user: CurrentUser,
    session: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
    keyword: str | None = None,
) -> ResponseEnvelope[PaginationData[SpeciesResponse]]:
    """List the authenticated user's personal species."""
    items, total = await list_species(session, current_user.id, pagination, keyword)
    data = build_pagination(
        [SpeciesResponse.model_validate(item) for item in items], total, pagination
    )
    return success_response(data)


@classification_router.post(
    "/species",
    response_model=ResponseEnvelope[SpeciesResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_species_view(
    request: SpeciesCreateRequest, current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[SpeciesResponse]:
    """Create a private species record."""
    item = await create_species(session, current_user.id, request)
    await session.commit()
    return success_response(SpeciesResponse.model_validate(item))


@classification_router.patch(
    "/species/{species_uuid}", response_model=ResponseEnvelope[SpeciesResponse]
)
async def update_species_view(
    species_uuid: UUID, request: SpeciesUpdateRequest, current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[SpeciesResponse]:
    """Update one private species record."""
    item = await update_species(session, current_user.id, species_uuid, request)
    await session.commit()
    return success_response(SpeciesResponse.model_validate(item))


@classification_router.delete("/species/{species_uuid}", response_model=ResponseEnvelope[None])
async def delete_species_view(
    species_uuid: UUID, current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[None]:
    """Soft-delete one private species record."""
    await soft_delete_species(session, current_user.id, species_uuid)
    await session.commit()
    return success_response()


@classification_router.get("/genes", response_model=ResponseEnvelope[list[GeneResponse]])
async def list_genes_view(
    current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[list[GeneResponse]]:
    """List the authenticated user's genes."""
    items = await list_genes(session, current_user.id)
    return success_response([GeneResponse.model_validate(item) for item in items])


@classification_router.post(
    "/genes", response_model=ResponseEnvelope[GeneResponse], status_code=status.HTTP_201_CREATED
)
async def create_gene_view(
    request: GeneCreateRequest, current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[GeneResponse]:
    """Create one personal gene."""
    item = await create_gene(session, current_user.id, request)
    await session.commit()
    return success_response(GeneResponse.model_validate(item))


@classification_router.patch("/genes/{gene_uuid}", response_model=ResponseEnvelope[GeneResponse])
async def update_gene_view(
    gene_uuid: UUID, request: GeneUpdateRequest, current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[GeneResponse]:
    """Update one personal gene."""
    item = await update_gene(session, current_user.id, gene_uuid, request)
    await session.commit()
    return success_response(GeneResponse.model_validate(item))


@classification_router.delete("/genes/{gene_uuid}", response_model=ResponseEnvelope[None])
async def delete_gene_view(
    gene_uuid: UUID, current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[None]:
    """Soft-delete one personal gene."""
    await soft_delete_gene(session, current_user.id, gene_uuid)
    await session.commit()
    return success_response()


@classification_router.get(
    "/identification-tags", response_model=ResponseEnvelope[list[TagResponse]]
)
async def list_tags_view(
    current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[list[TagResponse]]:
    """List the authenticated user's identification tags."""
    items = await list_tags(session, current_user.id)
    return success_response([TagResponse.model_validate(item) for item in items])


@classification_router.post(
    "/identification-tags",
    response_model=ResponseEnvelope[TagResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_tag_view(
    request: TagCreateRequest, current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[TagResponse]:
    """Create one personal identification tag."""
    item = await create_tag(session, current_user.id, request)
    await session.commit()
    return success_response(TagResponse.model_validate(item))


@classification_router.patch(
    "/identification-tags/{tag_uuid}", response_model=ResponseEnvelope[TagResponse]
)
async def update_tag_view(
    tag_uuid: UUID, request: TagUpdateRequest, current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[TagResponse]:
    """Update one personal identification tag."""
    item = await update_tag(session, current_user.id, tag_uuid, request)
    await session.commit()
    return success_response(TagResponse.model_validate(item))


@classification_router.delete("/identification-tags/{tag_uuid}", response_model=ResponseEnvelope[None])
async def delete_tag_view(
    tag_uuid: UUID, current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[None]:
    """Soft-delete one personal identification tag."""
    await soft_delete_tag(session, current_user.id, tag_uuid)
    await session.commit()
    return success_response()
