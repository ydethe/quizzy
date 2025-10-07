from typing import Any, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
import httpx
import jwt
from jwt import PyJWKClient
from pydantic import BaseModel

from .config import config

# OAuth2 scheme
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=config.AUTHORIZATION_URL,
    tokenUrl=config.TOKEN_URL,
)

# User model
class User(BaseModel):
    sub: str
    email: str
    name: str
    preferred_username: str
    groups: list[str] = []


# In-memory session storage (use Redis in production)
sessions = {}


async def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token from Authentik"""
    try:
        # Get JWKS from Authentik
        jwks_client = PyJWKClient(config.JWKS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Decode and verify token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=config.CLIENT_ID,
            options={"verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}"
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from token"""
    await verify_token(token)

    # Get additional user info from userinfo endpoint
    async with httpx.AsyncClient() as client:
        response = await client.get(
            config.USERINFO_URL, headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not fetch user info"
            )
        user_info = response.json()

    return User(
        sub=user_info.get("sub"),
        email=user_info.get("email", ""),
        name=user_info.get("name", ""),
        preferred_username=user_info.get("preferred_username", ""),
        groups=user_info.get("groups", []),
    )
