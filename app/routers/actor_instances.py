from uuid import uuid4
from fastapi import (APIRouter,
                    #  Depends,
                     HTTPException)
from pydantic import BaseModel

from dat_core.pydantic_models.connector_specification import ConnectorSpecification
from dat_core.pydantic_models.configured_document_stream import ConfiguredDocumentStream
from dat_core.db_models.workspaces import Workspace
from dat_core.db_models.actor_instances import ActorInstance as ActorInstanceModel
# from ..dependencies import get_token_header


from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from ..database import Base, get_db
# from ..models import ActorInstance as ActorInstanceModel

Base = declarative_base()



class ActorInstance(BaseModel):
    uuid: str
    connector_specification: ConnectorSpecification


router = APIRouter(
    prefix="/actor_instances",
    tags=["actor_instances"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


actor_instances_db = [{"name": "Wikipedia", "connectionSpecification": {}}]
actor_instances_db = []


@router.get("/{actor_type}/list")
async def fetch_available_actor_instances(actor_type: str) -> list[ConnectorSpecification]:
    return actor_instances_db


@router.get("/{actor_instance_uuid}")
async def read_actor_instance(actor_instance_uuid: str) -> ConnectorSpecification:
    """Will be populated from manifest file in verified-actor_instances repo"""
    return actor_instances_db[0]


@router.post("/",
    # responses={403: {"description": "Operation forbidden"}},
)
async def create_actor_instance(name: str, connector_specification: ConnectorSpecification) -> ActorInstance:
    actor_instance = {
        'id': str(uuid4()),
        'workspace_id': 'uuid',
        'actor_id': 'uuid',
        'user_id': 'uuid',
        'name': name,
        'actor_type': 'source',
        'configuration': connector_specification.model_dump_json(),
    }
    try:
        db = list(get_db())[0]
        db_actor_instance = ActorInstanceModel(**actor_instance)
        db.add(db_actor_instance)
        db.commit()
        db.refresh(db_actor_instance)
        return ActorInstance(uuid=actor_instance['id'], connector_specification=connector_specification).model_dump_json()
    except Exception as e:
        raise
        raise HTTPException(status_code=403, detail="Operation forbidden")
    # actor_instances_db.append(ActorInstance(
    #     uuid=, connector_specification=connector_specification))
    


@router.put(
    "/{actor_instance_uuid}",
    responses={403: {"description": "Operation forbidden"}},
)
async def update_actor_instance(actor_instance_uuid:str, 
                                conn_spec: ConnectorSpecification,
                                configured_document_stream: ConfiguredDocumentStream) -> list[ActorInstance]:
    for idx in range(len(actor_instances_db)):
        actor_instance = actor_instances_db[idx]
        if actor_instance_uuid != actor_instance.uuid:
            continue
        actor_instances_db[idx] = ActorInstance(
            uuid=str(uuid4()), connector_specification=conn_spec)
    return actor_instances_db

@router.delete(
    "/{actor_instance_uuid}",
    responses={403: {"description": "Operation forbidden"}},
)
async def delete_actor_instance(actor_instance_uuid: str) -> list[ActorInstance]:
    return {}


@router.get("/{actor_instance_uuid}/discover")
async def call_actor_instance_discover(actor_slug: str):
    """Initialize actor obj from verified-actors repo and call discover() on it and return"""
    return {}
