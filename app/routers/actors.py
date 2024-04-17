import yaml
# from uuid import uuid4
from datetime import datetime
import urllib.request
# import psycopg2
from fastapi import (APIRouter,
                     #  Depends,
                     HTTPException)
from pydantic import BaseModel

from dat_core.pydantic_models.connector_specification import ConnectorSpecification
from ..db_models.actors import Actor as ActorModel
# from ..dependencies import get_token_header

from ..database import get_db
# from ..models import Actor as ActorModel


class ActorInstance(BaseModel):
    uuid: str
    connector_specification: ConnectorSpecification


class Actor(BaseModel):
    id: str
    name: str
    icon: str = None
    actor_type: str
    status: str
    created_at: datetime
    updated_at: datetime





router = APIRouter(
    prefix="/actors",
    tags=["actors"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


def fetch_available_actors_from_db(
    actor_type: str = None,
    actor_uuid: str = None,
) -> list[Actor]:
    db = list(get_db())[0]
    query = db.query(ActorModel)
    if actor_type:
        query = query.filter(ActorModel.actor_type == actor_type)
    if actor_uuid:
        query = query.filter(ActorModel.id == actor_uuid)

    actors = query.all()

    if not actors:
        raise HTTPException(
            status_code=404, detail=f"No actors found for type {actor_type}")

    return actors


@router.get("/{actor_type}/list")
async def fetch_available_actors(actor_type: str) -> list:
    return [{
        'id': _.id,
        'name': _.name,
        } for _ in fetch_available_actors_from_db(actor_type)]


@router.get("/{actor_uuid}/specs")
async def get_actor_specs(actor_uuid: str):
    """Initialize actor obj from verified-actors repo and call spec() on it and return"""

    matching_actors = [
        _ for _ in fetch_available_actors_from_db(actor_uuid=actor_uuid)
        if _.id == actor_uuid
    ]
    if not matching_actors:
        raise HTTPException(status_code=404, detail="actor not found")
    with urllib.request.urlopen(f'https://raw.githubusercontent.com/dat-labs/verified-sources/main/verified_sources/{matching_actors[0].module_name}/specs.yml') as response:
        return yaml.safe_load(response.read().decode())
