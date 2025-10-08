from typing import Any, Dict
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
import httpx

from quizzy.auth import User, get_current_user
from quizzy.config import config


app = FastAPI(title="FastAPI with Authentik OAuth2")


@app.get("/")
async def root() -> Dict[str, str]:
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
        f"{config.AUTHORIZATION_URL}?"
        f"client_id={config.CLIENT_ID}&"
        f"redirect_uri={config.REDIRECT_URI}&"
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
            config.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": config.REDIRECT_URI,
                "client_id": config.CLIENT_ID,
                "client_secret": config.CLIENT_SECRET,
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange code for token : '{token_response.text}'",
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
    return {"message": "This is a protected route", "user": current_user.model_dump()}


@app.get("/admin")
async def admin_route(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Admin-only endpoint - requires admin group"""
    if "admin" not in current_user.groups:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return {"message": "This is an admin-only route", "user": current_user.model_dump()}


@app.get("/me")
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Get current user information"""
    return current_user


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
