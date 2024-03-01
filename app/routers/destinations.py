from fastapi import APIRouter, Depends, HTTPException

# from ..dependencies import get_token_header

router = APIRouter(
    prefix="/destinations",
    tags=["destinations"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


fake_destinations_db = {"plumbus": {
    "name": "Plumbus"}, "gun": {"name": "Portal Gun"}}


@router.get("/")
async def read_destinations():
    return fake_destinations_db


@router.get("/{destination_id}")
async def read_destination(destination_id: int):
    """Will be populated from manifest file in verified-destinations repo"""
    if destination_id not in fake_destinations_db:
        raise HTTPException(status_code=404, detail="destination not found")
    return {"name": fake_destinations_db[destination_id]["name"], "destination_id": destination_id}


@router.post(
    "/{destination_id}",
    responses={403: {"description": "Operation forbidden"}},
)
async def create_destination(destination_id: int):
    if destination_id != "plumbus":
        raise HTTPException(
            status_code=403, detail="You can only update the destination: plumbus"
        )
    return {"destination_id": destination_id, "name": "The great Plumbus"}


@router.put(
    "/{destination_id}",
    # tags=["custom"],
    responses={403: {"description": "Operation forbidden"}},
)
async def update_destination(destination_id: int):
    if destination_id != "plumbus":
        raise HTTPException(
            status_code=403, detail="You can only update the destination: plumbus"
        )
    return {"destination_id": destination_id, "name": "The great Plumbus"}


@router.get("/{destination_id}/specs")
async def get_destination_specs(destination_id: int):
    """Initialize destination obj from verified-destinations repo and call spec() on it and return"""
    if destination_id not in fake_destinations_db:
        raise HTTPException(status_code=404, detail="destination not found")
    return {"name": fake_destinations_db[destination_id]["name"], "destination_id": destination_id}


@router.get("/{destination_id}/discover")
async def call_destination_discover(destination_id: int):
    """Initialize destination obj from verified-destinations repo and call discover() on it and return"""
    return {"name": fake_destinations_db[destination_id]["name"], "destination_id": destination_id}
