import yaml
import urllib.request
from fastapi import (APIRouter,
                     HTTPException)
from ..models.actor_model import (
    ActorResponse, ActorPostRequest, ActorPutRequest
)
from ..db_models.actors import Actor as ActorModel
from ..database import get_db


router = APIRouter(
    prefix="/actors",
    tags=["actors"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


def fetch_available_actors_from_db(
    actor_type: str = None,
    actor_id: str = None,
) -> list[ActorResponse]:
    """
    Fetches available actors from the database based on the provided filters.

    Args:
        actor_type (str, optional): The type of actor to filter by. Defaults to None.
        actor_id (str, optional): The ID of the actor to filter by. Defaults to None.

    Returns:
        list[ActorResponse]: A list of ActorResponse objects representing the available actors.

    Raises:
        HTTPException: If no actors are found for the specified actor_type.

    """
    db = list(get_db())[0]
    query = db.query(ActorModel)
    if actor_type:
        query = query.filter(ActorModel.actor_type == actor_type)
    if actor_id:
        query = query.filter(ActorModel.id == actor_id)

    actors = query.all()

    if not actors:
        raise HTTPException(
            status_code=404, detail=f"No actors found for type {actor_type}")

    return actors


@router.get("/{actor_type}/list",
            response_model=list[ActorResponse],
            description="Fetch all active actors")
async def fetch_available_actors(actor_type: str) -> list[ActorResponse]:
    """
    Fetches all active actors of a specific type.

    Args:
        actor_type (str): The type of actor to fetch.

    Returns:
        list[ActorResponse]: A list of ActorResponse objects representing the available actors.

    """
    return fetch_available_actors_from_db(actor_type)


@router.get("/{actor_id}",
            response_model=ActorResponse)
async def read_actor(actor_id: str) -> ActorResponse:
    """
    Reads an actor based on its ID.

    Args:
        actor_id (str): The ID of the actor to read.

    Returns:
        ActorResponse: The ActorResponse object representing the actor.

    Raises:
        HTTPException: If the actor with the specified ID is not found.

    """
    matching_actors = fetch_available_actors_from_db(actor_id=actor_id)
    if not matching_actors:
        raise HTTPException(status_code=404, detail="actor not found")
    return matching_actors[0]


@router.post("", response_model=ActorResponse)
async def create_actor(payload: ActorPostRequest) -> ActorResponse:
    """
    Creates a new actor.

    Args:
        payload (ActorPostRequest): The payload containing the data for the new actor.

    Returns:
        ActorResponse: The ActorResponse object representing the created actor.

    Raises:
        HTTPException: If there is an error creating the actor.

    """
    db = list(get_db())[0]
    try:
        actor_instance = ActorModel(**payload.model_dump())
        db.add(actor_instance)
        db.commit()
        db.refresh(actor_instance)
        return actor_instance
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{actor_id}",
            response_model=ActorResponse)
async def update_actor(actor_id: str, payload: ActorPutRequest) -> ActorResponse:
    """
    Updates an existing actor.

    Args:
        actor_id (str): The ID of the actor to update.
        payload (ActorPutRequest): The payload containing the updated data for the actor.

    Returns:
        ActorResponse: The ActorResponse object representing the updated actor.

    Raises:
        HTTPException: If there is an error updating the actor.

    """
    db = list(get_db())[0]
    try:
        actor_instance = db.query(ActorModel).get(actor_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(actor_instance, key, value)
        db.commit()
        db.refresh(actor_instance)
        return actor_instance
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{actor_id}/mark_inactive")
async def mark_actor_inactive(actor_id: str) -> None:
    """
    Marks an actor as inactive.

    Args:
        actor_id (str): The ID of the actor to mark as inactive.

    Raises:
        HTTPException: If there is an error marking the actor as inactive.

    """
    try:
        db = list(get_db())[0]
        actor_instance = db.query(ActorModel).get(actor_id)
        actor_instance.status = "inactive"
        db.add(actor_instance)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{actor_id}")
async def delete_actor(actor_id: str) -> None:
    """
    Deletes an actor.

    Args:
        actor_id (str): The ID of the actor to delete.

    Raises:
        HTTPException: If there is an error deleting the actor.

    """
    try:
        db = list(get_db())[0]
        actor_instance = db.query(ActorModel).get(actor_id)
        db.delete(actor_instance)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{actor_uuid}/specs")
async def get_actor_specs(actor_uuid: str):
    """
    Retrieves the specifications of an actor.

    Args:
        actor_uuid (str): The UUID of the actor.

    Returns:
        dict: The specifications of the actor.

    Raises:
        HTTPException: If the actor with the specified UUID is not found.

    """
    matching_actors = [
        _ for _ in fetch_available_actors_from_db(actor_id=actor_uuid)
        if _.id == actor_uuid
    ]
    if not matching_actors:
        raise HTTPException(status_code=404, detail="actor not found")
    with urllib.request.urlopen(
        f"https://raw.githubusercontent.com/dat-labs/verified-sources"
        f"/main/verified_sources/{matching_actors[0].module_name}/specs.yml"
    ) as response:
        return yaml.safe_load(response.read().decode())
