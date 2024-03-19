from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from ..db_models.connections import (
    Connection as ConnectionInstanceModel)
from ..database import get_db


class ConnectionRequestInstance(BaseModel):
    name: Optional[str] = None
    source_instance_id: str
    generator_instance_id: str
    destination_instance_id: str
    configuration: Optional[dict] = None
    catalog: Optional[dict] = None
    cron_string: Optional[str] = None
    status: Optional[str] = None


class ConnectionResponseInstance(BaseModel):
    id: str
    name: str
    source_instance_id: str
    generator_instance_id: str
    destination_instance_id: str
    configuration: Optional[dict] = None
    catalog: Optional[dict] = None
    cron_string: Optional[str] = None
    status: str


router = APIRouter(
    prefix="/connections",
    tags=["connections"],
    responses={404: {"description": "Not found"}},
)

@router.get("/list/",
            response_model=list[ConnectionResponseInstance])
async def fetch_available_connections(
) -> list[ConnectionResponseInstance]:
    db = list(get_db())[0]
    connections = db.query(ConnectionInstanceModel).all()
    return connections


@router.get("/{connection_id}/",
            response_model=ConnectionResponseInstance)
async def read_connection(
    connection_id: str
) -> ConnectionResponseInstance:
    db = list(get_db())[0]
    connection = db.query(ConnectionInstanceModel).get(connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection


@router.post("/",
             responses={403: {"description": "Operation forbidden"}},
             response_model=ConnectionResponseInstance)
async def create_connection(
    payload: ConnectionRequestInstance
) -> ConnectionResponseInstance:
    try:
        db = list(get_db())[0]
        connection_instance = ConnectionInstanceModel(**payload.model_dump())
        db.add(connection_instance)
        db.commit()
        db.refresh(connection_instance)
        return connection_instance
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{connection_id}",
            responses={403: {"description": "Operation forbidden"}},
            response_model=ConnectionResponseInstance)
async def update_connection(
    connection_id: str,
    payload: ConnectionRequestInstance
) -> ConnectionResponseInstance:
    db = list(get_db())[0]
    try:
        connection_instance = db.query(ConnectionInstanceModel).get(connection_id)
        if connection_instance is None:
            raise HTTPException(status_code=404, detail="Connection not found")

        for key, value in payload.items():
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
        # Retrieve the connection instance
        connection_instance = db.query(ConnectionInstanceModel).get(connection_id)
        if connection_instance is None:
            raise HTTPException(status_code=404, detail="Connection not found")

        # Delete the connection instance
        db.delete(connection_instance)
        db.commit()

        return None
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

# @router.post("/{connection_id}/run")
# async def connection_trigger_run(connection_id: int):
#     # if connection_id not in fake_connections_db:
#     #     raise HTTPException(status_code=404, detail="connection not found")
#     app.send_task('dat_worker_task', (open(
#         'connection.json').read(), ), queue='dat-worker-q')
#     return json.loads(open('connection.json').read())


# @router.get("/{connection_id}/runs")
# async def get_connection_runs():
#     return fake_connections_db


# @router.get("/{connection_id}/runs/{run_id}")
# async def get_connection_runs_by_run_id():
#     return fake_connections_db
