from fastapi import APIRouter, Depends, HTTPException

# from ..dependencies import get_token_header

router = APIRouter(
    prefix="/sources",
    tags=["sources"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


fake_sources_db = {"plumbus": {
    "name": "Plumbus"}, "gun": {"name": "Portal Gun"}}


@router.get("/")
async def read_sources():
    return fake_sources_db


@router.get("/{source_id}")
async def read_source(source_id: int):
    """Will be populated from manifest file in verified-sources repo"""
    if source_id not in fake_sources_db:
        raise HTTPException(status_code=404, detail="source not found")
    return {"name": fake_sources_db[source_id]["name"], "source_id": source_id}


@router.post(
    "/{source_id}",
    responses={403: {"description": "Operation forbidden"}},
)
async def create_source(source_id: int):
    if source_id != "plumbus":
        raise HTTPException(
            status_code=403, detail="You can only update the source: plumbus"
        )
    return {"source_id": source_id, "name": "The great Plumbus"}


@router.put(
    "/{source_id}",
    # tags=["custom"],
    responses={403: {"description": "Operation forbidden"}},
)
async def update_source(source_id: int):
    if source_id != "plumbus":
        raise HTTPException(
            status_code=403, detail="You can only update the source: plumbus"
        )
    return {"source_id": source_id, "name": "The great Plumbus"}


@router.get("/{source_id}/specs")
async def get_source_specs(source_id: int):
    """Initialize source obj from verified-sources repo and call spec() on it and return"""
    if source_id not in fake_sources_db:
        raise HTTPException(status_code=404, detail="source not found")
    return {"name": fake_sources_db[source_id]["name"], "source_id": source_id}


@router.get("/{source_id}/discover")
async def call_source_discover(source_id: int):
    """Initialize source obj from verified-sources repo and call discover() on it and return"""
    return {"name": fake_sources_db[source_id]["name"], "source_id": source_id}
