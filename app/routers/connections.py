from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_token_header

router = APIRouter(
    prefix="/connections",
    tags=["connections"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


fake_connections_db = {"plumbus": {
    "name": "Plumbus"}, "gun": {"name": "Portal Gun"}}


@router.get("/")
async def read_connections():
    """
    ------------
    [S]->[G]->[D]
    ------------
    [S1]->[G1]->[D1]
    ------------
    """
    return fake_connections_db


# @router.get("/{connection_id}")
# async def read_connection(connection_id: int):
#     if connection_id not in fake_connections_db:
#         raise HTTPException(status_code=404, detail="connection not found")
#     return {"name": fake_connections_db[connection_id]["name"], "connection_id": connection_id}


@router.post("/", 
            responses={403: {"description": "Operation forbidden"}},)
async def create_connection(src_actor_instance_id: str,
                            gen_actor_instance_id: str,
                            dst_actor_instance_id: str,):
    return {"connection_id": str(uuid4()), "name": "The great Plumbus"}


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


@router.post("/{connection_id}/runs")
async def trigger_run_on_connection(connection_id: int):
    if connection_id not in fake_connections_db:
        raise HTTPException(status_code=404, detail="connection not found")
    return {"name": fake_connections_db[connection_id]["name"], "connection_id": connection_id}


@router.get("/{connection_id}/runs")
async def get_connection_runs():
    return fake_connections_db


@router.get("/{connection_id}/runs/{run_id}")
async def get_connection_runs_by_run_id():
    return fake_connections_db
