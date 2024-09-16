from importlib import import_module
from celery import Celery
import pydantic_core
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)
from app.db_models.connections import (
    Connection as ConnectionModel
)
from sqlalchemy.orm import joinedload
from app.db_models.connection_run_logs import ConnectionRunLogs
from app.db_models.actor_instances import ActorInstance as ActorInstanceModel
from app.database import get_db
from app.common.utils import CustomModel
from app.models.connection_model import (
    ConnectionResponse, ConnectionPostRequest,
    ConnectionPutRequest, ConnectionOrchestraResponse
)
from app.internal.connections import fetch_connection_config
from app.routers.actor_instances import get_actor_instance

app = Celery('tasks', broker='amqp://mq_user:mq_pass@message-queue:5672//')

router = APIRouter(
    prefix="/connections",
    tags=["connections"],
    responses={404: {"description": "Not found"}},
)


@router.get("/list",
            response_model=list[ConnectionResponse],
            description="Fetch all active connections")
async def fetch_available_connections(
        db=Depends(get_db),
        workspace_id: Optional[str] = Query(None, description="The workspace ID to scope the request")
) -> list[ConnectionResponse]:
    """
    Fetches all active connections from the database within a specific workspace,
    including related source, generator, and destination instances.

    Args:
        db (Session): The database session.
        workspace_id (str): The ID of the workspace to which the connections belong.

    Returns:
        list[ConnectionResponse]: A list of active connections with related instances.
    """
    try:
        query = db.query(ConnectionModel).filter(
            ConnectionModel.status.in_(["active", "inactive"]))

        if workspace_id:
            query = query.filter(ConnectionModel.workspace_id == workspace_id)

        connections = query.options(
            joinedload(ConnectionModel.source_instance),
            joinedload(ConnectionModel.generator_instance),
            joinedload(ConnectionModel.destination_instance)
        ).order_by(ConnectionModel.created_at.desc()).all()

        return connections
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{connection_id}",
            response_model=ConnectionResponse)
async def read_connection(
    connection_id: str,
    db = Depends(get_db),
    workspace_id: str = Query(..., description="The workspace ID to scope the request")
) -> ConnectionResponse:
    """
    Retrieves a connection by its ID within a specific workspace.

    Args:
        connection_id (str): The ID of the connection.
        db (Session): The database session.
        workspace_id (str): The ID of the workspace to which the connection belongs.

    Returns:
        ConnectionResponse: The connection with the specified ID.

    Raises:
        HTTPException: If the connection is not found or an error occurs.
    """
    try:
        connection = (
            db.query(ConnectionModel)
            .filter_by(id=connection_id, workspace_id=workspace_id)  # Scope by workspace_id
            .options(
                joinedload(ConnectionModel.source_instance),
                joinedload(ConnectionModel.generator_instance),
                joinedload(ConnectionModel.destination_instance)
            )
            .one_or_none()
        )

        if connection is None:
            raise HTTPException(status_code=404, detail="Connection not found")

        return connection

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("",
             responses={403: {"description": "Operation forbidden"}},
             response_model=ConnectionResponse)
async def create_connection(
    payload: ConnectionPostRequest,
    db=Depends(get_db),
    workspace_id: str = Query(..., description="The workspace ID to scope the request")
) -> ConnectionResponse:
    """
    Creates a new connection within a specific workspace.

    Args:
        payload (ConnectionPostRequest): The request payload containing the connection details.
        db (Session): The database session.
        workspace_id (str): The ID of the workspace to which the connection will belong.

    Returns:
        ConnectionResponse: The created connection.

    Raises:
        HTTPException: If the operation is forbidden or an error occurs.
    """
    actor_instance = db.query(ActorInstanceModel).filter_by(
        id=payload.source_instance_id, workspace_id=workspace_id  # Scope by workspace_id
    ).one_or_none()

    if actor_instance is None:
        raise HTTPException(status_code=404, detail="Actor instance not found")

    try:
        validate_catalog(actor_instance, payload.catalog)    
    except (pydantic_core._pydantic_core.ValidationError, 
            ImportError, AttributeError) as _e:
        raise HTTPException(status_code=403, detail=str(_e))

    try:
        connection_instance = ConnectionModel(
            **payload.model_dump(exclude={'catalog'}),
            catalog=CustomModel.convert_enums_to_str(payload.catalog.model_dump()),
            workspace_id=workspace_id  # Set workspace_id
        )
        db.add(connection_instance)
        db.commit()
        db.refresh(connection_instance)
        return connection_instance
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{connection_id}",
            responses={403: {"description": "Operation forbidden"}})
async def update_connection(
    connection_id: str,
    payload: ConnectionPutRequest,
    db=Depends(get_db),
    workspace_id: str = Query(..., description="The workspace ID to scope the request")
):
    """
    Updates an existing connection within a specific workspace.

    Args:
        connection_id (str): The ID of the connection to update.
        payload (ConnectionPutRequest): The request payload containing the updated connection details.
        db (Session): The database session.
        workspace_id (str): The ID of the workspace to which the connection belongs.

    Returns:
        The updated connection.

    Raises:
        HTTPException: If the connection is not found or an error occurs.
    """
    actor_instance = db.query(ActorInstanceModel).filter_by(
        id=payload.source_instance_id, workspace_id=workspace_id  # Scope by workspace_id
    ).one_or_none()

    if actor_instance is None:
        raise HTTPException(status_code=404, detail="Actor instance not found")

    try:
        validate_catalog(actor_instance, payload.catalog)    
    except (pydantic_core._pydantic_core.ValidationError, 
            ImportError, AttributeError) as _e:
        raise HTTPException(status_code=403, detail=str(_e))

    try:
        connection_instance = db.query(ConnectionModel).filter_by(
            id=connection_id, workspace_id=workspace_id  # Scope by workspace_id
        ).one_or_none()

        if connection_instance is None:
            raise HTTPException(status_code=404, detail="Connection not found")

        for key, value in payload.model_dump(exclude_unset=True).items():
            if key in ['source_instance_id']:
                continue
            setattr(connection_instance, key, value)

        db.add(connection_instance)
        db.commit()
        db.refresh(connection_instance)

        return connection_instance
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{connection_id}",
               responses={404: {"description": "Connection not found"}},
               status_code=204)
async def delete_connection(
    connection_id: str,
    db=Depends(get_db),
    workspace_id: str = Query(..., description="The workspace ID to scope the request")
) -> None:
    """
    Deletes a connection within a specific workspace.

    Args:
        connection_id (str): The ID of the connection to delete.
        db (Session): The database session.
        workspace_id (str): The ID of the workspace to which the connection belongs.

    Raises:
        HTTPException: If the connection is not found or an error occurs.
    """
    try:
        connection_instance = db.query(ConnectionModel).filter_by(
            id=connection_id, workspace_id=workspace_id  # Scope by workspace_id
        ).one_or_none()

        if connection_instance is None:
            raise HTTPException(status_code=404, detail="Connection not found")

        db.delete(connection_instance)
        db.commit()

        return None
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{connection_id}/run",
             response_model=ConnectionOrchestraResponse,
             description="Trigger the run for the connection")
async def connection_trigger_run(
    connection_id: str,
    workspace_id: Optional[str] = Query(None, description="The workspace ID to scope the request")
) -> ConnectionOrchestraResponse:
    """
    Triggers a run for the specified connection within a specific workspace.

    Args:
        connection_id (str): The ID of the connection.
        workspace_id (str): The ID of the workspace to which the connection belongs.

    Returns:
        ConnectionOrchestraResponse: The response from the connection orchestration.

    Raises:
        HTTPException: If the connection is not found or an error occurs.
    """
    resp = await fetch_connection_config(connection_id)
    app.send_task('dat_worker_task', (resp.model_dump_json(), ), queue='dat-worker-q')
    return resp.model_dump()


def validate_catalog(actor_instance, catalog):
    """
    Validates a catalog instance against the expected Catalog class for a given actor.

    This function dynamically imports the Catalog class based on the `actor_type`, `module_name`,
    and `name` attributes of the actor within the `actor_instance`. It then uses this Catalog
    class to validate the provided `catalog` by calling its `model_validate_json` method with
    the JSON representation of the catalog.

    Args:
        actor_instance: A db instance containing actor-related information, including `actor_type`,
            `module_name`, and `name`.
        catalog: The catalog instance to be validated.

    Raises:
        ImportError: If the specified module cannot be imported.
        AttributeError: If the specified Catalog class cannot be found in the module.
        pydantic_core._pydantic_core.ValidationError: If the catalog validation fails.

    Returns:
        None
    """
    CatalogClass = getattr(
        import_module(f'verified_{actor_instance.actor.actor_type}s.{actor_instance.actor.module_name}.catalog'), f'{actor_instance.actor.name}Catalog')
    CatalogClass.model_validate_json(catalog.model_dump_json())
    