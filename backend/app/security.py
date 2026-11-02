import os
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv

load_dotenv()

# Define the custom header key we will look for
API_KEY_NAME = "X-Internal-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

INTERNAL_API_SECRET = os.getenv("INTERNAL_API_SECRET")

async def validate_api_key(api_key: str = Security(api_key_header)):
    """
    Middleware validator that checks incoming headers for a valid API token.
    Ensures ONLY your Next.js server can execute backend graph actions.
    """
    if not INTERNAL_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server Misconfiguration: INTERNAL_API_SECRET is missing on backend."
        )
        
    if not api_key or api_key != INTERNAL_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Invalid or missing server access token."
        )
    return api_key
