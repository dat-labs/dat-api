import json
from celery import Celery
from fastapi import APIRouter, HTTPException
from ..db_models.connections import (
    Connection as ConnectionModel
)
from ..database import get_db
from ..common.utils import CustomModel
from ..models.connection_model import (
    ConnectionResponse, ConnectionPostRequest,
    ConnectionPutRequest, ConnectionOrchestraResponse
)
from ..internal.connections import fetch_connection_config

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
) -> list[ConnectionResponse]:
    db = list(get_db())[0]

    connections = db.query(ConnectionModel).filter_by(status='active').all()
    return connections


@router.get("/{connection_id}",
            response_model=ConnectionResponse)
async def read_connection(
    connection_id: str
) -> ConnectionResponse:
    db = list(get_db())[0]
    connection = db.query(ConnectionModel).get(connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection


@router.post("",
             responses={403: {"description": "Operation forbidden"}},
             response_model=ConnectionResponse)
async def create_connection(
    payload: ConnectionPostRequest
) -> ConnectionResponse:
    try:
        db = list(get_db())[0]
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
    payload: ConnectionPutRequest
) -> ConnectionResponse:
    db = list(get_db())[0]
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
    connection_id: str
) -> None:
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
async def connection_trigger_run(
    connection_id: str
) -> ConnectionOrchestraResponse:
    """
    Call /internal/connections/{connection_id} endpoint
    to get the connection configuration and trigger the run
    """
    resp = await fetch_connection_config(connection_id)
    app.send_task('dat_worker_task', (resp.json(), ), queue='dat-worker-q')
    return resp.model_dump()


# @router.get("/{connection_id}/runs")
# async def get_connection_runs():
#     return fake_connections_db


# @router.get("/{connection_id}/runs/{run_id}")
# async def get_connection_runs_by_run_id():
#     return fake_connections_db
