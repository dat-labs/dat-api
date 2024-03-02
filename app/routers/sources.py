from uuid import uuid4
from fastapi import (APIRouter,
                    #  Depends,
                     HTTPException)
from pydantic import BaseModel

from dat_core.pydantic_models.connector_specification import ConnectorSpecification
# from ..dependencies import get_token_header


class SourceInstance(BaseModel):
    uuid: str
    connector_specification: ConnectorSpecification


router = APIRouter(
    prefix="/sources",
    tags=["sources"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


sources_db = [{"name": "Wikipedia", "connectionSpecification": {}}]
source_instances_db = []


@router.get("/available")
async def fetch_available_sources() -> list[ConnectorSpecification]:
    return sources_db


@router.get("/{source_slug}")
async def read_available_source(source_slug: str) -> ConnectorSpecification:
    """Will be populated from manifest file in verified-sources repo"""
    return sources_db[0]


@router.post(
    "/{source_slug}/create-instance",
    responses={403: {"description": "Operation forbidden"}},
)
async def create_source_instance(source_slug: str, conn_spec: ConnectorSpecification) -> list[SourceInstance]:
    source_instances_db.append(SourceInstance(
        uuid=str(uuid4()), connector_specification=conn_spec))
    return source_instances_db


@router.put(
    "/{source_slug}/update-instance/{source_instance_uuid}",
    responses={403: {"description": "Operation forbidden"}},
)
async def update_source_instance(source_slug: str, source_instance_uuid:
                                 str, conn_spec: ConnectorSpecification) -> list[SourceInstance]:
    for idx in range(len(source_instances_db)):
        source_instance = source_instances_db[idx]
        if source_instance_uuid != source_instance.uuid:
            continue
        source_instances_db[idx] = SourceInstance(
            uuid=str(uuid4()), connector_specification=conn_spec)
    return source_instances_db


@router.get("/{source_slug}/specs")
async def get_source_specs(source_slug: str):
    """Initialize source obj from verified-sources repo and call spec() on it and return"""
    if source_slug not in sources_db:
        raise HTTPException(status_code=404, detail="source not found")
    return {"name": sources_db[source_slug]["name"], "source_id": source_slug}


@router.get("/{source_slug}/discover")
async def call_source_discover(source_slug: str):
    """Initialize source obj from verified-sources repo and call discover() on it and return"""
    return {"name": sources_db[source_slug]["name"], "source_id": source_slug}
