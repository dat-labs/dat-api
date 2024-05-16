from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from importlib import import_module
from typing import List
from dat_core.pydantic_models.connector_specification import ConnectorSpecification
from app.db_models.actors import Actor as ActorModel
from app.db_models.actor_instances import ActorInstance as ActorInstanceModel
from app.db_models.connections import Connection as ConnectionModel
from pydantic import ValidationError
from app.database import get_db
from app.models.actor_instance_model import (
    ActorInstanceResponse, ActorInstancePostRequest,
    ActorInstancePutRequest, ActorInstanceGetResponse
)


router = APIRouter(
    prefix="/actor_instances",
    tags=["actor_instances"],
    responses={404: {"description": "Not found"}},
    # dependencies=[Depends(get_db)]
)

def get_actor_instance(db, actor_instance_id: str):
    '''
    Function to get actor instance for an actor_id.
    TODO: refactor the code for routers into a seperate service class
    '''
    actor_instance = db.query(ActorInstanceModel).get(actor_instance_id)
    if actor_instance is None:
        raise HTTPException(status_code=404, detail="Actor instance not found")
    _actor = db.query(ActorModel).get(actor_instance.actor_id)
    connected_connections = [
        connection.to_dict()
        for connection in db.query(ConnectionModel).filter_by(
            **{ACTOR_TYPE_ID_MAP[_actor.actor_type]: actor_instance.id}
        ).all()
    ]

    return ActorInstanceGetResponse(
        **actor_instance.to_dict(),
        actor=_actor.to_dict(),
        connected_connections=connected_connections
    )

ACTOR_TYPE_ID_MAP = {
    "source": "source_instance_id",
    "generator": "generator_instance_id",
    "destination": "destination_instance_id"
}

@router.get(
        "/{actor_type}/list",
        response_model=list[ActorInstanceGetResponse],
        description="Fetch all active actors"
)
async def fetch_available_actor_instances(
    actor_type: str,
    db=Depends(get_db)
) -> List[ActorInstanceGetResponse]:
    try:
        actor_instances = db.query(ActorInstanceModel).filter_by(
            actor_type=actor_type).all()

        for actor_instance in actor_instances:
            actor_instance.actor = db.query(ActorModel).get(actor_instance.actor_id)
            connected_connections = [
                connection.to_dict()
                for connection in db.query(ConnectionModel).filter_by(
                    **{ACTOR_TYPE_ID_MAP[actor_type]: actor_instance.id}
                ).all()
            ]
            actor_instance.connected_connections = connected_connections
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return actor_instances

@router.get(
        "/{actor_instance_id}",
        response_model=ActorInstanceGetResponse
)
async def read_actor_instance(
    actor_instance_id: str,
    db=Depends(get_db)
) -> ActorInstanceGetResponse:
    # actor_instance = db.query(ActorInstanceModel).get(actor_instance_id)
    # if actor_instance is None:
    #     raise HTTPException(status_code=404, detail="Actor instance not found")
    # _actor = db.query(ActorModel).get(actor_instance.actor_id)
    # connected_connections = [
    #     connection.to_dict()
    #     for connection in db.query(ConnectionModel).filter_by(
    #         **{ACTOR_TYPE_ID_MAP[_actor.actor_type]: actor_instance.id}
    #     ).all()
    # ]

    # return ActorInstanceGetResponse(
    #     **actor_instance.to_dict(),
    #     actor=_actor.to_dict(),
    #     connected_connections=connected_connections
    # )
    return get_actor_instance(db, actor_instance_id)


@router.post("",
             responses={403: {"description": "Operation forbidden"}},
             response_model=ActorInstanceResponse
)
async def create_actor_instance(
    payload: ActorInstancePostRequest,
    db=Depends(get_db)
) -> ActorInstanceResponse:
    try:
        db_actor_instance = ActorInstanceModel(
            **payload.model_dump(exclude_unset=True)
        )
        db.add(db_actor_instance)
        db.commit()
        db.refresh(db_actor_instance)
        return ActorInstanceResponse(
            **db_actor_instance.to_dict(),
            actor=db.query(ActorModel).get(db_actor_instance.actor_id).to_dict()
        )
    except ValidationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put(
    "/{actor_instance_id}",
    responses={403: {"description": "Operation forbidden"}},
    response_model=ActorInstanceResponse
)
async def update_actor_instance(
    actor_instance_id: str,
    payload: ActorInstancePutRequest,
    db=Depends(get_db)
) -> ActorInstanceResponse:
    """
    Update an actor instance.

    Args:
        actor_instance_id (str): The ID of the actor instance to update.
        payload (ActorInstancePutRequest): The updated data for the actor instance.
        db (Database): The database session.

    Returns:
        ActorInstanceResponse: The updated actor instance.

    Raises:
        HTTPException: If the actor instance is not found or if there
        is a validation error or an exception occurs.
    """
    actor_instance = db.query(ActorInstanceModel).get(actor_instance_id)
    if actor_instance is None:
        raise HTTPException(status_code=404, detail="Actor instance not found")
    try:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(actor_instance, key, value)
        db.commit()
        db.refresh(actor_instance)
        return ActorInstanceResponse(
            **actor_instance.to_dict(),
            actor=db.query(ActorModel).get(actor_instance.actor_id).to_dict()
        )
    except ValidationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{actor_instance_id}",
    responses={403: {"description": "Operation forbidden"}},
)
async def delete_actor_instance(
    actor_instance_id: str,
    db=Depends(get_db)
) -> None:
    actor_instance = db.query(ActorInstanceModel).get(actor_instance_id)
    if actor_instance is None:
        raise HTTPException(status_code=404, detail="Actor instance not found")
    try:
        db.delete(actor_instance)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{actor_instance_uuid}/discover")
async def call_actor_instance_discover(
    actor_instance_uuid: str,
    db=Depends(get_db)
):
    actor_instance = db.query(ActorInstanceModel).get(actor_instance_uuid)
    connector_specification = ConnectorSpecification(
        name=actor_instance.actor.name,
        module_name=actor_instance.actor.module_name,
        connection_specification=actor_instance.configuration,
    )
    SourceClass = getattr(
        import_module(f'verified_{actor_instance.actor.actor_type}s.{actor_instance.actor.module_name}.{actor_instance.actor.actor_type}'), actor_instance.actor.name)

    catalog = SourceClass().discover(config=connector_specification)
    return catalog
