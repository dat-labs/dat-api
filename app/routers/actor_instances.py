import json
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

Base = declarative_base()


class ActorInstance(BaseModel):
    uuid: str = str(uuid4())
    name: str
    workspace_id: str = 'wkspc-uuid'            # setting defaults
    actor_id: str = 'gdrive-uuid'               # will remove them
    user_id: str = 'user-uuid'                  # later
    configuration: ConnectorSpecification


router = APIRouter(
    prefix="/actor_instances",
    tags=["actor_instances"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


actor_instances_db = [{"name": "Wikipedia", "connectionSpecification": {}}]
actor_instances_db = []


@router.get("/{actor_type}/list")
async def fetch_available_actor_instances(actor_type: str) -> list[ActorInstance]:
    db = list(get_db())[0]
    aai = db.query(ActorInstanceModel).filter_by(actor_type=actor_type).all()
    if not aai:
        raise HTTPException(
            status_code=404, detail=f"No actor instances with actor_type: {actor_type} found")
    return aai


@router.get("/{actor_instance_uuid}")
async def read_actor_instance(actor_instance_uuid: str) -> ActorInstance:
    db = list(get_db())[0]
    ai = db.query(ActorInstanceModel).get(actor_instance_uuid)
    if not ai:
        raise HTTPException(
            status_code=404, detail=f'Actor instances with id: {actor_instance_uuid} NOT found')
    return ai


@router.post("/",
             responses={403: {"description": "Operation forbidden"}},
             )
async def create_actor_instance(actor_instance: ActorInstance) -> ActorInstance:
    actor_instance_dct = {
        'id': actor_instance.uuid,
        'workspace_id': actor_instance.workspace_id,
        'actor_id': actor_instance.actor_id,
        'user_id': actor_instance.user_id,
        'name': actor_instance.name,
        'actor_type': 'source',
        'configuration': json.loads(actor_instance.configuration.model_dump_json()),
    }
    try:
        db = list(get_db())[0]
        db_actor_instance = ActorInstanceModel(**actor_instance_dct)
        db.add(db_actor_instance)
        db.commit()
        db.refresh(db_actor_instance)
        # return {1: 2}
        return actor_instance
    except Exception as e:
        raise
        raise HTTPException(status_code=403, detail="Operation forbidden")
    # actor_instances_db.append(ActorInstance(
    #     uuid=, connector_specification=connector_specification))


@router.put(
    "/{actor_instance_uuid}",
    responses={403: {"description": "Operation forbidden"}},
)
async def update_actor_instance(actor_instance_uuid: str,
                                conn_spec: ConnectorSpecification,
                                configured_document_stream: ConfiguredDocumentStream) -> list[ActorInstance]:
    for idx in range(len(actor_instances_db)):
        actor_instance = actor_instances_db[idx]
        if actor_instance_uuid != actor_instance.uuid:
            continue
        actor_instances_db[idx] = ActorInstance(
            uuid=str(uuid4()), connector_specification=conn_spec)
    return actor_instances_db


@router.delete("/{actor_instance_uuid}",
    responses={403: {"description": "Operation forbidden"}},
)
async def delete_actor_instance(actor_instance_uuid: str) -> dict:
    db = list(get_db())[0]
    db.query(ActorInstanceModel).filter_by(id=actor_instance_uuid).delete()
    db.commit()
    return {'msg': f'actor instance with id: {actor_instance_uuid} DELETED'}


@router.get("/{actor_instance_uuid}/discover")
async def call_actor_instance_discover(actor_slug: str):
    """Initialize actor obj from verified-actors repo and call discover() on it and return"""
    return {}
