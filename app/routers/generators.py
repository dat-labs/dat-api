from fastapi import APIRouter, Depends, HTTPException

# from ..dependencies import get_token_header

router = APIRouter(
    prefix="/generators",
    tags=["generators"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


fake_generators_db = {"plumbus": {
    "name": "Plumbus"}, "gun": {"name": "Portal Gun"}}


@router.get("/")
async def read_generators():
    return fake_generators_db


@router.get("/{generator_id}")
async def read_generator(generator_id: int):
    """Will be populated from manifest file in verified-generators repo"""
    if generator_id not in fake_generators_db:
        raise HTTPException(status_code=404, detail="generator not found")
    return {"name": fake_generators_db[generator_id]["name"], "generator_id": generator_id}


@router.post(
    "/{generator_id}",
    responses={403: {"description": "Operation forbidden"}},
)
async def create_generator(generator_id: int):
    if generator_id != "plumbus":
        raise HTTPException(
            status_code=403, detail="You can only update the generator: plumbus"
        )
    return {"generator_id": generator_id, "name": "The great Plumbus"}


@router.put(
    "/{generator_id}",
    # tags=["custom"],
    responses={403: {"description": "Operation forbidden"}},
)
async def update_generator(generator_id: int):
    if generator_id != "plumbus":
        raise HTTPException(
            status_code=403, detail="You can only update the generator: plumbus"
        )
    return {"generator_id": generator_id, "name": "The great Plumbus"}


@router.get("/{generator_id}/specs")
async def get_generator_specs(generator_id: int):
    """Initialize generator obj from verified-generators repo and call spec() on it and return"""
    if generator_id not in fake_generators_db:
        raise HTTPException(status_code=404, detail="generator not found")
    return {"name": fake_generators_db[generator_id]["name"], "generator_id": generator_id}

