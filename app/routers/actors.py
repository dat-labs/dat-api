from uuid import uuid4
from fastapi import (APIRouter,
                    #  Depends,
                     HTTPException)
from pydantic import BaseModel

from dat_core.pydantic_models.connector_specification import ConnectorSpecification
# from ..dependencies import get_token_header


class ActorInstance(BaseModel):
    uuid: str
    connector_specification: ConnectorSpecification


router = APIRouter(
    prefix="/actors",
    tags=["actors"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


actors_db = [{"name": "Wikipedia", "connectionSpecification": {}}]
actor_instances_db = []


@router.get("/{actor_type}/list")
async def fetch_available_actors(actor_type: str) -> list[ConnectorSpecification]:
    return actors_db


# @router.get("/{actor_slug}")
# async def read_available_actor(actor_slug: str) -> ConnectorSpecification:
#     """Will be populated from manifest file in verified-actors repo"""
#     return actors_db[0]



@router.get("/{actor_slug}/specs")
async def get_actor_specs(actor_slug: str):
    """Initialize actor obj from verified-actors repo and call spec() on it and return"""
    if actor_slug not in actors_db:
        raise HTTPException(status_code=404, detail="actor not found")
    return {"name": actors_db[actor_slug]["name"], "actor_id": actor_slug}


