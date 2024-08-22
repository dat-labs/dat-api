from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)
from importlib import import_module
from typing import List, Optional
from dat_core.pydantic_models.connector_specification import ConnectorSpecification
from app.db_models.actors import Actor as ActorModel
from app.db_models.actor_instances import ActorInstance as ActorInstanceModel
from app.db_models.connections import Connection as ConnectionModel
from pydantic import ValidationError
from app.database import get_db
from app.models.actor_instance_model import (
    ActorInstanceResponse, ActorInstancePostRequest,
    ActorInstancePutRequest,
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

    return ActorInstanceResponse(
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
        response_model=list[ActorInstanceResponse],
        description="Fetch all active actors"
)
async def fetch_available_actor_instances(
    actor_type: str,
    db=Depends(get_db)
) -> List[ActorInstanceResponse]:
    try:
        actor_instances = db.query(ActorInstanceModel).filter_by(
            actor_type=actor_type,
            status="active"
        ).order_by(ActorInstanceModel.created_at.desc()).all()

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
        response_model=ActorInstanceResponse
)
async def read_actor_instance(
    actor_instance_id: str,
    db=Depends(get_db)
) -> ActorInstanceResponse:
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


@router.post(
    "",
    responses={403: {"description": "Operation forbidden"}},
    response_model=ActorInstanceResponse
)
async def create_actor_instance(
    payload: ActorInstancePostRequest,
    db = Depends(get_db)
) -> ActorInstanceResponse:
    """
    Create a new actor instance after testing the connection.

    Args:
        payload (ActorInstancePostRequest): The data for the new actor instance.
        db (Session): The database session.

    Returns:
        ActorInstanceResponse: The created actor instance.

    Raises:
        HTTPException: If there is a validation error or an exception occurs.
    """
    try:
        db_actor_instance = ActorInstanceModel(**payload.model_dump())
        db.add(db_actor_instance)

        # Test the connection
        actor = db.query(ActorModel).get(db_actor_instance.actor_id)
        if actor is None:
            raise HTTPException(status_code=404, detail="Actor not found")

        SourceClass = getattr(
        import_module(
            f'verified_{actor.actor_type}s.{actor.module_name}.{actor.actor_type}'),
            actor.name
        )
        config = ConnectorSpecification(
            name=actor.name,
            module_name=actor.module_name,
            connection_specification=db_actor_instance.configuration
        )
        check_connection_tpl = SourceClass().check(config)
        if check_connection_tpl.status.name != 'SUCCEEDED':
            raise HTTPException(status_code=403, detail=check_connection_tpl.message)

        db.commit()
        db.refresh(db_actor_instance)

        return ActorInstanceResponse(
            **db_actor_instance.to_dict(),
            actor=db.query(ActorModel).get(db_actor_instance.actor_id).to_dict(),
            connected_connections=[]
        )

    except ValidationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.patch(
    "/{actor_instance_id}",
    responses={403: {"description": "Operation forbidden"}, 404: {"description": "Actor instance not found"}},
    response_model=ActorInstanceResponse
)
async def update_actor_instance(
    actor_instance_id: str,
    payload: ActorInstancePutRequest,
    db = Depends(get_db)
) -> ActorInstanceResponse:
    """
    Update an existing actor instance after testing the connection.

    Args:
        actor_instance_id (str): The ID of the actor instance to update.
        payload (ActorInstancePutRequest): The updated data for the actor instance.
        db (Session): The database session.

    Returns:
        ActorInstanceResponse: The updated actor instance.

    Raises:
        HTTPException: If the actor instance is not found, or if a validation error or exception occurs.
    """
    actor_instance = db.query(ActorInstanceModel).get(actor_instance_id)
    if actor_instance is None:
        raise HTTPException(status_code=404, detail="Actor instance not found")

    try:
        # Update fields
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(actor_instance, key, value)

        # Test the connection with updated configuration
        actor = db.query(ActorModel).get(actor_instance.actor_id)
        if actor is None:
            raise HTTPException(status_code=404, detail="Actor not found")

        SourceClass = getattr(
            import_module(f'verified_{actor.actor_type}s.{actor.module_name}.{actor.actor_type}'),
            actor.name
        )
        config = ConnectorSpecification(
            name=actor.name,
            module_name=actor.module_name,
            connection_specification=actor_instance.configuration
        )
        check_connection_tpl = SourceClass().check(config)
        if check_connection_tpl.status.name != 'SUCCEEDED':
            raise HTTPException(status_code=403, detail=check_connection_tpl.message)

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
