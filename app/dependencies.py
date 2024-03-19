from typing import Annotated
import jwt
from fastapi import Header, HTTPException


async def get_token_header(x_token: Annotated[str, Header()]):
    try:
        jwt.decode(x_token, 'secret', algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")

async def get_query_token(token: str):
    if token != "jessica":
        raise HTTPException(status_code=400, detail="No Jessica token provided")
