from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
import requests
from importlib import import_module
from app.models.actor_model import (
    ActorResponse, ActorPostRequest,
    ActorPutRequest
)
from app.db_models.actors import Actor as ActorModel
from app.database import get_db
from app.config import GITBOOK_ACCESS_TOKEN, GITBOOK_SPACE_ID


router = APIRouter(
    prefix="/actors",
    tags=["actors"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


def fetch_available_actors_from_db(
    actor_type: str = None,
    actor_id: str = None,
    db=None
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
    query = db.query(ActorModel)
    if actor_type:
        query = query.filter(ActorModel.actor_type == actor_type)
    if actor_id:
        query = query.filter(ActorModel.id == actor_id)

    try:
        actors = query.all()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not actors:
        return []

    return actors


@router.get(
    "/{actor_type}/list",
    response_model=list[ActorResponse],
    description="Fetch all active actors"
)
async def fetch_available_actors(
    actor_type: str,
    db=Depends(get_db)
) -> list[ActorResponse]:
    """
    Fetches all active actors of a specific type.

    Args:
        actor_type (str): The type of actor to fetch.

    Returns:
        list[ActorResponse]: A list of ActorResponse objects representing the available actors.

    """
    return fetch_available_actors_from_db(actor_type, db=db)


@router.get("/{actor_id}",
            response_model=ActorResponse)
async def read_actor(
    actor_id: str,
    db=Depends(get_db)
) -> ActorResponse:
    """
    Reads an actor based on its ID.

    Args:
        actor_id (str): The ID of the actor to read.

    Returns:
        ActorResponse: The ActorResponse object representing the actor.

    Raises:
        HTTPException: If the actor with the specified ID is not found.

    """
    matching_actors = fetch_available_actors_from_db(actor_id=actor_id, db=db)
    if not matching_actors:
        raise HTTPException(status_code=404, detail="actor not found")
    return matching_actors[0]


@router.post("", response_model=ActorResponse)
async def create_actor(
    payload: ActorPostRequest,
    db=Depends(get_db)
) -> ActorResponse:
    """
    Creates a new actor.

    Args:
        payload (ActorPostRequest): The payload containing the data for the new actor.

    Returns:
        ActorResponse: The ActorResponse object representing the created actor.

    Raises:
        HTTPException: If there is an error creating the actor.

    """
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
async def update_actor(
    actor_id: str,
    payload: ActorPutRequest,
    db=Depends(get_db)
) -> ActorResponse:
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
async def mark_actor_inactive(
    actor_id: str,
    db=Depends(get_db)
) -> None:
    """
    Marks an actor as inactive.

    Args:
        actor_id (str): The ID of the actor to mark as inactive.

    Raises:
        HTTPException: If there is an error marking the actor as inactive.

    """
    try:
        actor_instance = db.query(ActorModel).get(actor_id)
        actor_instance.status = "inactive"
        db.add(actor_instance)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{actor_id}")
async def delete_actor(
    actor_id: str,
    db=Depends(get_db)
) -> None:
    """
    Deletes an actor.

    Args:
        actor_id (str): The ID of the actor to delete.

    Raises:
        HTTPException: If there is an error deleting the actor.

    """
    try:
        actor_instance = db.query(ActorModel).get(actor_id)
        db.delete(actor_instance)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{actor_id}/spec")
async def get_actor_specs(
    actor_id: str,
    db=Depends(get_db)
):
    """
    Retrieves the specifications of an actor.

    Args:
        actor_id (str): The ID of the actor.

    Returns:
        dict: The specifications of the actor.

    Raises:
        HTTPException: If the actor with the specified UUID is not found.

    """
    matching_actors = [
        _ for _ in fetch_available_actors_from_db(actor_id=actor_id, db=db)
        if _.id == actor_id
    ]
    if not matching_actors:
        raise HTTPException(status_code=404, detail="actor not found")

    actor = matching_actors[0]
    SourceClass = getattr(
        import_module(f'verified_{actor.actor_type}s.{actor.module_name}.{actor.actor_type}'), actor.name)

    return SourceClass().spec()


@router.get("/doc/")
async def get_actor_documentaion(
    path: str,
) -> str:
    """
    Retrieves the documentation for an actor.

    Args:
        path (str): The path to the actor documentation.

    Returns:
        str: The documentation for the actor.
    """
    print(f"Fetching documentation for path {path}")
    page_id = _get_page_id_by_path(path)

    return _get_content_by_id(page_id)

def _get_page_id_by_path(page_path: str) -> str:
    top_path = "integrations"
    url = f"https://dat-serve-gitbook.riju.tech/v1/spaces/{GITBOOK_SPACE_ID}/content/path/{top_path}"

    # combine top path with the provided path
    combined_path = f"{top_path}/{page_path}"
    print(f"Fetching page ID for path {combined_path}")
    response = requests.request("GET", url)

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Content not found")

    page_path_parts = page_path.split('/')
    actor_type = page_path_parts[0]
    actor_name = page_path_parts[1]

    for item in response.json().get('pages', []):
        if item.get('slug') == actor_type:
            for sub_item in item.get('pages', []):
                if sub_item.get('slug') == actor_name and sub_item.get('path') == combined_path:
                    return sub_item.get('id')
                elif sub_item.get('slug') == actor_name:
                    for sub_sub_item in sub_item.get('pages', []):
                        if sub_sub_item.get('path') == combined_path:
                            return sub_sub_item.get('id')

def _get_content_by_id(page_id: str) -> str:
    url = f"https://dat-serve-gitbook.riju.tech/v1/spaces/{GITBOOK_SPACE_ID}/content/page/{page_id}"

    print(f"Fetching content for page ID {page_id}")
    response = requests.request("GET", url)

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Content not found")

    return response.json().get('markdown', '')
