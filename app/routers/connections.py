import json
from uuid import uuid4
from celery import Celery
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from importlib import import_module
from ..db_models.connections import Connection as ConnectionInstanceModel


from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from ..database import get_db


app = Celery('tasks', broker='amqp://mq_user:mq_pass@message-queue:5672//')

router = APIRouter(
    prefix="/connections",
    tags=["connections"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.get("/{connection_id}/list")
async def read_connection(connection_id: str):
    db = list(get_db())[0]
    connection = db.query(ConnectionInstanceModel).get(connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection


@router.post("/", 
            responses={403: {"description": "Operation forbidden"}},)
async def create_connection(payload: Dict[str, Any]):
    src_actor_instance_id = payload['src_actor_instance_id']
    gen_actor_instance_id = payload['gen_actor_instance_id']
    dst_actor_instance_id = payload['dst_actor_instance_id']

    connection_instance_dct = {
        'source_instance_id': src_actor_instance_id,
        'generator_instance_id': gen_actor_instance_id,
        'destination_instance_id': dst_actor_instance_id,
        'name': 'Gdrive to Qdrant',
        'configuration': {"src_actor_instance_id": src_actor_instance_id,
                          "gen_actor_instance_id": gen_actor_instance_id,
                          "dst_actor_instance_id": dst_actor_instance_id}
    }   
    try:
        db = list(get_db())[0]
        connection_instance = ConnectionInstanceModel(**connection_instance_dct)
        db.add(connection_instance)
        db.commit()
        db.refresh(connection_instance)
        return connection_instance
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.put(
    "/{connection_id}",
    responses={403: {"description": "Operation forbidden"}},
)
async def update_connection(connection_id: int):
    if connection_id != "plumbus":
        raise HTTPException(
            status_code=403, detail="You can only update the connection: plumbus"
        )
    return {"connection_id": connection_id, "name": "The great Plumbus"}


@router.post("/{connection_id}/run")
async def connection_trigger_run(connection_id: int):
    # if connection_id not in fake_connections_db:
    #     raise HTTPException(status_code=404, detail="connection not found")
    app.send_task('dat_worker_task', (open(
        'connection.json').read(), ), queue='dat-worker-q')
    return json.loads(open('connection.json').read())


@router.get("/{connection_id}/runs")
async def get_connection_runs():
    return fake_connections_db


@router.get("/{connection_id}/runs/{run_id}")
async def get_connection_runs_by_run_id():
    return fake_connections_db
