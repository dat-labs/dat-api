import os
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query, UploadFile, File
)
from importlib import import_module
from typing import List, Optional
from pydantic import ValidationError
from minio import Minio
from minio.error import S3Error
from tempfile import NamedTemporaryFile
from dat_core.pydantic_models.connector_specification import ConnectorSpecification
from app.db_models.actors import Actor as ActorModel
from app.db_models.actor_instances import ActorInstance as ActorInstanceModel
from app.db_models.connections import Connection as ConnectionModel
from app.database import get_db
from app.models.actor_instance_model import (
    ActorInstanceResponse, ActorInstancePostRequest,
    ActorInstancePutRequest, UploadResponse
)

MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")

router = APIRouter(
    prefix="/actor_instances",
    tags=["actor_instances"],
    responses={404: {"description": "Not found"}},
    # dependencies=[Depends(get_db)]
)

def get_actor_instance(db, actor_instance_id: str, workspace_id: str):
    actor_instance = db.query(ActorInstanceModel).filter_by(
        id=actor_instance_id, workspace_id=workspace_id  # Scope by workspace_id
    ).first()
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
        description="Fetch all active actors in the workspace"
)
async def fetch_available_actor_instances(
    actor_type: str,
    workspace_id: str = Query(..., description="The workspace ID to scope the request"),
    db=Depends(get_db)
) -> List[ActorInstanceResponse]:
    """
    Fetches all active actors from the database.

    Args:
        actor_type: The type of actor to fetch.
        workspace_id: The ID of the workspace.

    Returns:
        A list of active actors with related instances.
    """
    try:
        actor_instances = db.query(ActorInstanceModel).filter_by(
            actor_type=actor_type,
            workspace_id=workspace_id,  # Scope by workspace_id
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
    workspace_id: str = Query(..., description="The workspace ID to scope the request"),
    db=Depends(get_db)
) -> ActorInstanceResponse:
    return get_actor_instance(db, actor_instance_id, workspace_id)


@router.post(
    "",
    responses={403: {"description": "Operation forbidden"}},
    response_model=ActorInstanceResponse
)
async def create_actor_instance(
    payload: ActorInstancePostRequest,
    workspace_id: str = Query(..., description="The workspace ID to scope the request"),
    db=Depends(get_db)
) -> ActorInstanceResponse:
    """
    Create a new actor instance after testing the connection.

    Args:
        payload (ActorInstancePostRequest): The data for the actor instance.
        workspace_id (str): The ID of the workspace.
        db (Session): The database session.

    Returns:
        ActorInstanceResponse: The created actor instance.
    """
    try:
        db_actor_instance = ActorInstanceModel(**payload.model_dump(), workspace_id=workspace_id)
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
    db = Depends(get_db),
    workspace_id: str = Query(..., description="The workspace ID to scope the request")
) -> ActorInstanceResponse:
    """
    Update an existing actor instance within a specific workspace after testing the connection.

    Args:
        actor_instance_id (str): The ID of the actor instance to update.
        payload (ActorInstancePutRequest): The updated data for the actor instance.
        db (Session): The database session.
        workspace_id (str): The ID of the workspace to which the actor instance belongs.

    Returns:
        ActorInstanceResponse: The updated actor instance.

    Raises:
        HTTPException: If the actor instance is not found, or if a validation error or exception occurs.
    """
    actor_instance = db.query(ActorInstanceModel).filter_by(
        id=actor_instance_id, workspace_id=workspace_id  # Scope by workspace_id
    ).first()

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
        connected_connections = [
            connection.to_dict()
            for connection in db.query(ConnectionModel).filter_by(
                **{ACTOR_TYPE_ID_MAP[actor.actor_type]: actor_instance.id}
            ).all()
        ]
        return ActorInstanceResponse(
            **actor_instance.to_dict(),
            actor=db.query(ActorModel).get(actor_instance.actor_id).to_dict(),
            connected_connections=connected_connections
        )

    except ValidationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/{actor_instance_id}",
    responses={403: {"description": "Operation forbidden"},
               404: {"description": "Actor instance not found"}}
)
async def delete_actor_instance(
    actor_instance_id: str,
    db=Depends(get_db),
    workspace_id: str = Query(..., description="The workspace ID to scope the request")
) -> None:
    """
    Delete an existing actor instance within a specific workspace.

    Args:
        actor_instance_id (str): The ID of the actor instance to delete.
        db (Session): The database session.
        workspace_id (str): The ID of the workspace to which the actor instance belongs.

    Raises:
        HTTPException: If the actor instance is not found or an exception occurs.
    """
    actor_instance = db.query(ActorInstanceModel).filter_by(
        id=actor_instance_id, workspace_id=workspace_id  # Scope by workspace_id
    ).first()

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
    db=Depends(get_db),
    workspace_id: str = Query(..., description="The workspace ID to scope the request")
):
    """
    Discover available data or schema for an actor instance within a specific workspace.

    Args:
        actor_instance_uuid (str): The UUID of the actor instance to discover.
        db (Session): The database session.
        workspace_id (str): The ID of the workspace to which the actor instance belongs.

    Returns:
        The discovered catalog or data schema for the actor instance.
    """
    actor_instance = db.query(ActorInstanceModel).filter_by(
        id=actor_instance_uuid, workspace_id=workspace_id  # Scope by workspace_id
    ).first()

    if actor_instance is None:
        raise HTTPException(status_code=404, detail="Actor instance not found")

    connector_specification = ConnectorSpecification(
        name=actor_instance.actor.name,
        module_name=actor_instance.actor.module_name,
        connection_specification=actor_instance.configuration,
    )

    SourceClass = getattr(
        import_module(f'verified_{actor_instance.actor.actor_type}s.{actor_instance.actor.module_name}.{actor_instance.actor.actor_type}'),actor_instance.actor.name)

    catalog = SourceClass().discover(config=connector_specification)
    return catalog

@router.get("/{actor_instance_id}/check")
async def call_actor_instance_check(
    actor_instance_id: str,
    db=Depends(get_db),
    workspace_id: str = Query(..., description="The workspace ID to scope the request")
):
    """
    Check the connection for an actor instance within a specific workspace.

    Args:
        actor_instance_id (str): The ID of the actor instance to check.
        db (Session): The database session.
        workspace_id (str): The ID of the workspace to which the actor instance belongs.

    Returns:
        The connection status for the actor instance.
    """
    actor_instance = db.query(ActorInstanceModel).filter_by(
        id=actor_instance_id, workspace_id=workspace_id  # Scope by workspace_id
    ).first()

    if actor_instance is None:
        raise HTTPException(status_code=404, detail="Actor instance not found")

    connector_specification = ConnectorSpecification(
        name=actor_instance.actor.name,
        module_name=actor_instance.actor.module_name,
        connection_specification=actor_instance.configuration,
    )

    SourceClass = getattr(
        import_module(f"verified_{actor_instance.actor.actor_type}s."
                      f"{actor_instance.actor.module_name}.{actor_instance.actor.actor_type}"),actor_instance.actor.name)

    check_connection_tpl = SourceClass().check(config=connector_specification)
    if check_connection_tpl.status.name != 'SUCCEEDED':
        raise HTTPException(status_code=403, detail=check_connection_tpl.message)

    return check_connection_tpl


@router.post("/upload/", response_model=UploadResponse)
async def upload_file_to_minio(file: UploadFile = File(...), target_path: str = None):
    """
    Upload a file from a HTTP upload to MinIO.
    """
    try:
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ROOT_USER,
            secret_key=MINIO_ROOT_PASSWORD,
            secure=False
        )
        with NamedTemporaryFile(delete=False) as temp_file:
            # Write the uploaded file's content to the temp file
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()

            temp_file_path = temp_file.name

        minio_client.fput_object(
            MINIO_BUCKET_NAME,
            target_path or file.filename,
            temp_file_path
        )


        return UploadResponse(
            bucket_name=MINIO_BUCKET_NAME,
            uploaded_path=target_path or file.filename,
            message=f"File uploaded successfully to {target_path or file.filename} in bucket {MINIO_BUCKET_NAME}"
        )

    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO upload failed: {e}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
