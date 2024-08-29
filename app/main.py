from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# from .dependencies import get_query_token, get_token_header
from .internal import admin, connections as connections_internal
from .routers import (
    connections, actors,
    actor_instances, users,
    connection_run_logs, workspaces,
    organizations, workspace_users,
)
from .common.exceptions.exceptions import NotFound, Unauthorized
# from pydantic import BaseModel

app = FastAPI(
    # dependencies=[Depends(get_token_header)]
)


origins = ["*"]  # Replace with your allowed origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Adjust as needed
    allow_methods=["*"],  # Adjust as needed
    allow_headers=["*"],  # Adjust as needed
)

@app.exception_handler(NotFound)
async def not_found_exception_handler(request: Request, exc: NotFound):
    raise HTTPException(
            status_code=exc.status_code, detail=exc.to_dict())
    
@app.exception_handler(Unauthorized)
async def unauthorized_exception_handler(request: Request, exc: Unauthorized):
    raise HTTPException(
            status_code=exc.status_code, detail=exc.to_dict())

# base_router = APIRouter(
#     prefix="/workspaces/{workspace_id}",
# )
# base_router.include_router(connections.router)
# app.include_router(base_router)

app.include_router(
    connections_internal.router,
    prefix="/internal"
)
app.include_router(connections.router)
app.include_router(actors.router)
app.include_router(actor_instances.router)
app.include_router(connection_run_logs.router)
app.include_router(users.router)
app.include_router(workspaces.router)
app.include_router(organizations.router)
app.include_router(workspace_users.router)
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
