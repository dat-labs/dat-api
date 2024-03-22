from fastapi import Depends, FastAPI, Request, HTTPException
# from .dependencies import get_query_token, get_token_header
from .internal import admin
from .routers import (connections, 
                    #   sources, generators, destinations,
                      actors, actor_instances, users,
                      connection_run_logs,
                      )
from .common.exceptions.exceptions import NotFound, Unauthorized
# from pydantic import BaseModel

app = FastAPI(
    # dependencies=[Depends(get_token_header)]
)

@app.exception_handler(NotFound)
async def not_found_exception_handler(request: Request, exc: NotFound):
    raise HTTPException(
            status_code=exc.status_code, detail=exc.to_dict())
    
@app.exception_handler(Unauthorized)
async def unauthorized_exception_handler(request: Request, exc: Unauthorized):
    raise HTTPException(
            status_code=exc.status_code, detail=exc.to_dict())


# app.include_router(admin.router)
app.include_router(connections.router)
# app.include_router(sources.router)
# app.include_router(generators.router)
# app.include_router(destinations.router)
app.include_router(actors.router)
app.include_router(actor_instances.router)
app.include_router(connection_run_logs.router)
app.include_router(users.router)
app.include_router(
    admin.router,
    prefix="/admin",
    # tags=["admin"],
    # dependencies=[Depends(get_token_header)],
    # responses={418: {"description": "I'm a teapot"}},
)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}

# class Source(BaseModel):
#     pass
# class SourcesList(BaseModel):
#     data: List[Source]


# @app.get("/sources")
# async def get_sources() -> SourcesList:
#     """Will be populated from manifest file in verified-sources repo"""
#     return {"data": []}

# @app.get("/sources/{source_id}/specs")
# async def get_source_spec(source_id) -> SourcesList:
#     """Initialize source obj from verified-sources repo and call spec() on it and return

#     Args:
#         source_id (_type_): _description_

#     Returns:
#         SourcesList: _description_
#     """
#     return {"data": []}

# @app.get("/sources/{source_id}/discover")
# async def get_source_catalog(source_id) -> SourcesList:
#     """Initialize source obj from verified-sources repo and call discover() on it and return

#     Args:
#         source_id (_type_): _description_

#     Returns:
#         SourcesList: _description_
#     """
#     return {"data": []}

# @app.get("/generators")
# async def get_generators(connection_id) -> SourcesList:
#     return {"data": []}

# # @app.get("/generators/{generator_id}/specs")
    
# @app.get("/destinations")
# async def get_destinations(connection_id) -> SourcesList:
#     return {"data": []}

# # @app.get("/destinations/{destination_id}/specs")
# # @app.get("/destinations/{destination_id}/discover")

# # @app.post("/connections")
# # @app.get("/connections")
# """
# ------------
# [S]->[G]->[D]
# ------------
# [S1]->[G1]->[D1]
# ------------
# """
# # @app.get("/connections/{connection_id}")

# @app.get("/trigger-run/{connection_id}")
# async def trigger_run(connection_id):
#     return {"message": f"connection_id:{connection_id} triggered for execution"}

# # @app.get("/connections/{connection_id}/runs")

# # @app.get("/connections/{connection_id}/runs/{run_id}")