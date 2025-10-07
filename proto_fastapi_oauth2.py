from typing import Any, Dict
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.responses import RedirectResponse
import httpx
import jwt
from jwt import PyJWKClient
from pydantic import BaseModel
import os


# Configuration - Set these via environment variables
AUTHENTIK_URL = os.getenv("AUTHENTIK_URL", "https://authentik.company")
CLIENT_ID = os.getenv("CLIENT_ID", "your-client-id")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "your-client-secret")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/callback")

# OAuth2 endpoints
AUTHORIZATION_URL = f"{AUTHENTIK_URL}/application/o/authorize/"
TOKEN_URL = f"{AUTHENTIK_URL}/application/o/token/"
USERINFO_URL = f"{AUTHENTIK_URL}/application/o/userinfo/"
JWKS_URL = f"{AUTHENTIK_URL}/application/o/your-app-slug/jwks/"

app = FastAPI(title="FastAPI with Authentik OAuth2")

# OAuth2 scheme
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=AUTHORIZATION_URL,
    tokenUrl=TOKEN_URL,
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
        jwks_client = PyJWKClient(JWKS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Decode and verify token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
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
        response = await client.get(USERINFO_URL, headers={"Authorization": f"Bearer {token}"})
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


@app.get("/")
async def root():
    """Public endpoint"""
    return {
        "message": "Welcome to FastAPI with Authentik OAuth2",
        "login": "/login",
        "docs": "/docs",
    }


@app.get("/login")
async def login():
    """Redirect to Authentik login page"""
    auth_url = (
        f"{AUTHORIZATION_URL}?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid email profile"
    )
    return RedirectResponse(auth_url)


@app.get("/callback")
async def callback(code: str) -> Dict[str, Any]:
    """OAuth2 callback endpoint"""
    async with httpx.AsyncClient() as client:
        # Exchange authorization code for access token
        token_response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange code for token"
            )

        tokens = token_response.json()
        access_token = tokens.get("access_token")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "message": "Login successful! Use this token in Authorization header",
        }


@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Protected endpoint - requires authentication"""
    return {"message": "This is a protected route", "user": current_user.dict()}


@app.get("/admin")
async def admin_route(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Admin-only endpoint - requires admin group"""
    if "admin" not in current_user.groups:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return {"message": "This is an admin-only route", "user": current_user.dict()}


@app.get("/me")
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Get current user information"""
    return current_user


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
