from typing import List
from celery import Celery
from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from app.db_models.connections import (
    Connection as ConnectionModel
)
from app.db_models.connection_run_logs import ConnectionRunLogs
from app.database import get_db
from app.common.utils import CustomModel
from app.models.connection_model import (
    ConnectionResponse, ConnectionPostRequest,
    ConnectionPutRequest, ConnectionOrchestraResponse
)
from app.models.connection_run_log_model import ConnectionRunLogResponse
from app.internal.connections import fetch_connection_config

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
        db=Depends(get_db)
) -> list[ConnectionResponse]:
    """
    Fetches all active connections from the database.

    Returns:
        A list of active connections.
    """
    try:
        connections = db.query(ConnectionModel).filter_by(status='active').all()
        return connections
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{connection_id}",
            response_model=ConnectionResponse)
async def read_connection(
    connection_id: str,
    db=Depends(get_db)
) -> ConnectionResponse:
    """
    Retrieves a connection by its ID.

    Args:
        connection_id: The ID of the connection.

    Returns:
        The connection with the specified ID.

    Raises:
        HTTPException: If the connection is not found.
    """
    connection = db.query(ConnectionModel).get(connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection


@router.post("",
             responses={403: {"description": "Operation forbidden"}},
             response_model=ConnectionResponse)
async def create_connection(
    payload: ConnectionPostRequest,
    db=Depends(get_db)
) -> ConnectionResponse:
    """
    Creates a new connection.

    Args:
        payload: The request payload containing the connection details.

    Returns:
        The created connection.

    Raises:
        HTTPException: If the operation is forbidden or an error occurs.
    """
    try:
        connection_instance = ConnectionModel(
            **payload.model_dump(exclude={'catalog'}),
            catalog=CustomModel.convert_enums_to_str(payload.catalog.model_dump())
        )
        db.add(connection_instance)
        db.commit()
        db.refresh(connection_instance)
        return connection_instance
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{connection_id}",
            responses={403: {"description": "Operation forbidden"}},
            response_model=ConnectionResponse)
async def update_connection(
    connection_id: str,
    payload: ConnectionPutRequest,
    db=Depends(get_db)
) -> ConnectionResponse:
    """
    Updates an existing connection.

    Args:
        connection_id: The ID of the connection to update.
        payload: The request payload containing the updated connection details.

    Returns:
        The updated connection.

    Raises:
        HTTPException: If the connection is not found or an error occurs.
    """
    try:
        connection_instance = db.query(ConnectionModel).get(connection_id)
        if connection_instance is None:
            raise HTTPException(status_code=404, detail="Connection not found")

        print(payload.model_dump(exclude_unset=True))
        for key, value in payload.model_dump(exclude_unset=True).items():
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
    db=Depends(get_db)
) -> None:
    """
    Deletes a connection.

    Args:
        connection_id: The ID of the connection to delete.

    Raises:
        HTTPException: If the connection is not found or an error occurs.
    """
    db = list(get_db())[0]
    try:
        connection_instance = db.query(ConnectionModel).get(connection_id)
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
async def connection_trigger_run(\
    connection_id: str,
    db = Depends(get_db)
) -> ConnectionOrchestraResponse:
    """
    Triggers a run for the specified connection.

    Args:
        connection_id: The ID of the connection.

    Returns:
        The response from the connection orchestration.

    Raises:
        HTTPException: If the connection is not found or an error occurs.
    """
    resp = await fetch_connection_config(connection_id)
    app.send_task('dat_worker_task', (resp.model_dump_json(), ), queue='dat-worker-q')
    return resp.model_dump()


@router.post("/{connection_id}/runs",
             response_model=List[ConnectionRunLogResponse],
             description="Get all runs for a given connection id")
async def get_connection_run_logs(
    connection_id: str,
    db = Depends(get_db)
) -> List[ConnectionRunLogResponse]:
    db = list(get_db())[0]
    try:
        run_logs = db.query(ConnectionRunLogs).filter_by(connection_id=connection_id).all()
        return run_logs
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/runs/{run_id}",
            response_model=ConnectionRunLogResponse,
            description="Get a particular connection run log by id")
async def get_connection_run_by_run_id(
    connection_id: str,
    run_id: str
    ) -> ConnectionRunLogResponse:
    db = list(get_db())[0]
    try:
        run_log = db.query(ConnectionRunLogs).filter_by(connection_id=connection_id, id=run_id).first()
        return run_log
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

