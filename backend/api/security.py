import os
from fastapi import Header, HTTPException

async def api_key_auth(x_api_key: str = Header(None)):
    key = os.environ.get("API_KEY")
    if not key:
        return
    if x_api_key != key:
        raise HTTPException(status_code=401, detail="Unauthorized")