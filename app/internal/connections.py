from fastapi import APIRouter, HTTPException
from fastapi import Path
from dat_core.pydantic_models import ConnectorSpecification
from ..database import get_db
from ..db_models.connections import Connection as ConnectionModel
from ..db_models.actor_instances import ActorInstance as ActorInstanceModel
from ..db_models.actors import Actor as ActorModel
from ..models.connection_model import ConnectionOrchestraResponse

class APIError(HTTPException):
    def __init__(self, status_code: int, message: str):
        super().__init__(status_code=status_code, detail=message)


router = APIRouter(
    prefix="/connections",
    tags=["connections"],
    responses={404: {"description": "Not found"}},
)

async def get_connection_orchestra_response(connection_id: str) -> ConnectionOrchestraResponse:
    db_session = list(get_db())[0]
    connection = db_session.query(ConnectionModel).get(connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="Connection not found")

    _source = db_session.query(ActorInstanceModel).get(connection.source_instance_id)
    _generator = db_session.query(ActorInstanceModel).get(connection.generator_instance_id)
    _destination = db_session.query(ActorInstanceModel).get(connection.destination_instance_id)

    source_actor = db_session.query(ActorModel).get(_source.actor_id)
    generator_actor = db_session.query(ActorModel).get(_generator.actor_id)
    destination_actor = db_session.query(ActorModel).get(_destination.actor_id)

    source_actor_dct = {
        "name": source_actor.name,
        "module_name": source_actor.module_name,
        "connection_specification": _source.configuration
    }
    generator_actor_dct = {
        "name": generator_actor.name,
        "module_name": generator_actor.module_name,
        "connection_specification": _generator.configuration
    }
    destination_actor_dct = {
        "name": destination_actor.name,
        "module_name": destination_actor.module_name,
        "connection_specification": _destination.configuration
    }

    return ConnectionOrchestraResponse(
        **connection.to_dict(),
        source=ConnectorSpecification(**source_actor_dct).model_dump(),
        generator=ConnectorSpecification(**generator_actor_dct).model_dump(),
        destination=ConnectorSpecification(**destination_actor_dct).model_dump()
    )

@router.get("/{connection_id}",
            response_model=ConnectionOrchestraResponse,
            description="Fetch connection configuration for orchestra")
async def fetch_connection_config(
    connection_id: str = Path(..., description="The ID of the connection to fetch")
) -> ConnectionOrchestraResponse:
    try:
        return await get_connection_orchestra_response(connection_id)
    except Exception as e:
        raise APIError(status_code=500, message=str(e))
